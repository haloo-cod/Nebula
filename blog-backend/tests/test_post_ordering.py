"""博文列表排序：兼容旧日期格式，验证置顶、分页与同日稳定顺序。"""

from datetime import datetime

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_optional_current_user
from app.api.v1.posts import router
from app.database import get_db
from app.models import Base
from app.models.post import Post


@pytest_asyncio.fixture
async def post_client():
    """使用独立内存数据库访问真实文章列表路由。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            app = FastAPI()
            app.include_router(router, prefix="/api/v1")

            async def test_db():
                yield session

            app.dependency_overrides[get_db] = test_db
            app.dependency_overrides[get_optional_current_user] = lambda: None
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                yield client, session
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dates, expected",
    [
        (["2026-9-23", "2026-10-18"], [2, 1]),
        (["2026-9-3", "2026-9-23"], [2, 1]),
        (["2026-09-23", "2026-9-3"], [1, 2]),
        (["2025-12-31", "2026-1-1"], [2, 1]),
        (["", "2026-10-18"], [2, 1]),
    ],
)
async def test_post_dates_sort_chronologically(post_client, dates, expected):
    client, session = post_client
    session.add_all(
        Post(id=index, slug=f"post-{index}", title=f"文章 {index}", date=date)
        for index, date in enumerate(dates, start=1)
    )
    await session.commit()

    response = await client.get("/api/v1/posts")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == expected
    # 查询排序兼容旧格式，响应仍保留作者填写的原始日期。
    assert {item["id"]: item["date"] for item in items} == dict(
        enumerate(dates, start=1)
    )


@pytest.mark.asyncio
async def test_pinned_post_precedes_newer_unpinned_post(post_client):
    client, session = post_client
    session.add_all(
        [
            Post(id=1, slug="pinned", title="置顶旧文", date="2025-1-1", is_pinned=True),
            Post(id=2, slug="new", title="新文", date="2026-10-18"),
        ]
    )
    await session.commit()

    response = await client.get("/api/v1/posts")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [1, 2]


@pytest.mark.asyncio
async def test_same_day_uses_creation_time_then_id(post_client):
    client, session = post_client
    session.add_all(
        [
            Post(id=1, slug="older", title="较早创建", date="2026-9-23",
                 created_at=datetime(2026, 9, 23, 1)),
            Post(id=2, slug="later", title="较晚创建", date="2026-09-23",
                 created_at=datetime(2026, 9, 23, 2)),
            Post(id=3, slug="same-time", title="同时创建", date="2026-9-23",
                 created_at=datetime(2026, 9, 23, 2)),
        ]
    )
    await session.commit()

    response = await client.get("/api/v1/posts")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [3, 2, 1]


@pytest.mark.asyncio
async def test_category_pagination_follows_global_date_order_and_hides_drafts(post_client):
    client, session = post_client
    session.add_all(
        [
            Post(id=1, slug="early", title="九月上旬", date="2026-9-3", category="技术"),
            Post(id=2, slug="life", title="最新生活", date="2026-10-18", category="生活"),
            Post(id=3, slug="october", title="十月技术", date="2026-10-17", category="技术"),
            Post(id=4, slug="september", title="九月下旬", date="2026-9-23", category="技术"),
            Post(id=5, slug="draft", title="草稿", date="2026-12-1", category="技术", is_draft=True),
        ]
    )
    await session.commit()

    for page, expected_id in enumerate([3, 4, 1], start=1):
        response = await client.get(
            "/api/v1/posts", params={"category": "技术", "page": page, "page_size": 1}
        )
        assert response.status_code == 200
        assert response.json()["total"] == 3
        assert [item["id"] for item in response.json()["items"]] == [expected_id]

    response = await client.get("/api/v1/posts", params={"page_size": 2})
    assert response.status_code == 200
    assert response.json()["total"] == 4
    assert [item["id"] for item in response.json()["items"]] == [2, 3]
