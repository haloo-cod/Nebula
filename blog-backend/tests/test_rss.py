"""RSS 公开内容、日期、摘要、身份稳定性及交换友链配置的端到端验证。"""

from datetime import datetime
from email.utils import parsedate_to_datetime
import json
from types import SimpleNamespace
from urllib.parse import quote
from xml.etree import ElementTree as ET

from fastapi import FastAPI
import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.api.v1.router import router
from app.config import settings
from app.database import get_db
from app.models import Base
from app.models.post import Post
from app.models.site_config import SiteConfig


@pytest_asyncio.fixture
async def rss_client(monkeypatch):
    """真实 v1 路由配合独立内存数据库，避免触碰开发和生产数据。"""
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://blog.example.com/")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            app = FastAPI()
            app.include_router(router)

            async def test_db():
                yield session

            app.dependency_overrides[get_db] = test_db
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                yield client, session, app
    finally:
        await engine.dispose()


def feed_items(response):
    """由标准 XML 解析器检查返回结果，不依赖文本拼接的细节。"""
    assert response.status_code == 200
    root = ET.fromstring(response.content)
    assert root.tag == "rss" and root.attrib["version"] == "2.0"
    return root.find("channel"), root.findall("channel/item")


@pytest.mark.asyncio
async def test_public_feed_xml_metadata_urls_and_drafts(rss_client):
    client, session, _ = rss_client
    session.add_all([
        SiteConfig(key="friends_exchange_info", value=json.dumps({
            "name": "星夜 & <博客>", "bio": "介绍 & 思考", "rss_url": "https://feeds.example.com/custom"
        })),
        Post(id=1, slug="中文 &?#", title="中文 & <标题>", date="2026-10-20",
             description="摘要 & 简介", category="技术 & 生活", content_html="不应泄漏的完整正文"),
        Post(id=2, slug="draft", title="草稿机密", date="2026-12-1", is_draft=True),
    ])
    await session.commit()

    response = await client.get("/api/v1/rss.xml", headers={"Authorization": "Bearer ignored-for-public-feed"})
    channel, items = feed_items(response)
    assert response.headers["content-type"] == "application/rss+xml; charset=utf-8"
    assert response.headers["cache-control"] == "public, max-age=300"
    assert channel.findtext("title") == "星夜 & <博客>"
    assert channel.findtext("description") == "介绍 & 思考"
    assert channel.findtext("link") == "https://blog.example.com/"
    assert channel.find("{http://www.w3.org/2005/Atom}link").attrib["href"] == "https://blog.example.com/api/v1/rss.xml"
    assert len(items) == 1
    assert items[0].findtext("title") == "中文 & <标题>"
    assert items[0].findtext("description") == "摘要 & 简介"
    assert items[0].findtext("category") == "技术 & 生活"
    assert items[0].findtext("link") == "https://blog.example.com/post/" + quote("中文 &?#", safe="")
    assert items[0].find("guid").attrib["isPermaLink"] == "false"
    assert "完整正文" not in response.text and "草稿机密" not in response.text


@pytest.mark.asyncio
async def test_summary_fallback_is_visible_plaintext_and_limited(rss_client):
    client, session, _ = rss_client
    session.add(Post(slug="summary", title="摘要回退", description="  ",
                     content_html="<style>不应出现</style><script>隐藏脚本</script><h2>标题</h2><p>正文 &amp; 内容</p><p>" + "中" * 220 + "</p>"))
    await session.commit()
    _, items = feed_items(await client.get("/api/v1/rss.xml"))
    summary = items[0].findtext("description")
    assert summary.startswith("标题 正文 & 内容 ")
    assert len(summary) == 200
    assert "隐藏" not in summary and "不应出现" not in summary


@pytest.mark.asyncio
@pytest.mark.parametrize("value, expected", [
    ("2026-9-3", "2026-09-03T00:00:00+08:00"),
    ("2026-09-23", "2026-09-23T00:00:00+08:00"),
    ("", "2026-10-20T02:03:04+00:00"),
    ("2026-2-30", "2026-10-20T02:03:04+00:00"),
    ("not-a-date", "2026-10-20T02:03:04+00:00"),
])
async def test_publication_dates_use_beijing_and_utc_fallback(rss_client, value, expected):
    client, session, _ = rss_client
    session.add(Post(slug="date", title="日期", date=value, created_at=datetime(2026, 10, 20, 2, 3, 4)))
    await session.commit()
    _, items = feed_items(await client.get("/api/v1/rss.xml"))
    assert parsedate_to_datetime(items[0].findtext("pubDate")).isoformat() == expected


@pytest.mark.asyncio
async def test_chronological_order_limit_and_same_day_ties(rss_client):
    client, session, _ = rss_client
    for day in range(1, 24):
        session.add(Post(id=day, slug=f"day-{day}", title=f"day-{day}", date=f"2026-9-{day}",
                         is_pinned=day == 1, created_at=datetime(2026, 9, day)))
    session.add_all([
        Post(id=30, slug="october-earlier", title="october-earlier", date="2026-10-20", created_at=datetime(2026, 10, 20, 1)),
        Post(id=31, slug="october-later", title="october-later", date="2026-10-20", created_at=datetime(2026, 10, 20, 2)),
        Post(id=32, slug="october-tie", title="october-tie", date="2026-10-20", created_at=datetime(2026, 10, 20, 2)),
        Post(id=33, slug="fallback-newest", title="fallback-newest", date="bad", created_at=datetime(2026, 10, 21)),
    ])
    await session.commit()
    _, items = feed_items(await client.get("/api/v1/rss.xml"))
    assert len(items) == 20
    assert [item.findtext("title") for item in items[:5]] == ["fallback-newest", "october-tie", "october-later", "october-earlier", "day-23"]
    assert "day-1" not in [item.findtext("title") for item in items]


@pytest.mark.asyncio
async def test_guid_survives_edits_but_distinguishes_reused_ids(rss_client):
    client, session, _ = rss_client
    post = Post(id=1, slug="original", title="原题", date="2026-10-20", created_at=datetime(2026, 10, 20))
    session.add(post)
    await session.commit()
    _, items = feed_items(await client.get("/api/v1/rss.xml"))
    guid = items[0].findtext("guid")
    post.slug, post.title, post.description, post.date = "edited", "改题", "新摘要", "2026-10-19"
    await session.commit()
    _, items = feed_items(await client.get("/api/v1/rss.xml"))
    assert items[0].findtext("guid") == guid
    await session.delete(post)
    await session.commit()
    session.add(Post(id=1, slug="replacement", title="另一篇", created_at=datetime(2026, 10, 21)))
    await session.commit()
    _, items = feed_items(await client.get("/api/v1/rss.xml"))
    assert items[0].findtext("guid") != guid


@pytest.mark.asyncio
async def test_empty_feed_and_blank_channel_metadata_have_defaults(rss_client):
    client, session, _ = rss_client
    session.add(SiteConfig(key="friends_exchange_info", value='{"name":" ","bio":""}'))
    await session.commit()
    channel, items = feed_items(await client.get("/api/v1/rss.xml"))
    assert channel.findtext("title") == "Starlitn'blog"
    assert channel.findtext("description") == "分享技术、生活和思考的个人博客"
    assert items == []


@pytest.mark.asyncio
async def test_config_legacy_json_round_trip_clear_and_other_fields(rss_client):
    client, session, app = rss_client
    legacy = {"name": "站名", "url": "https://example.com", "avatar": "avatar.png", "bio": "简介", "requirements": ["原创"], "contact": "hello@example.com"}
    record = SiteConfig(key="friends_exchange_info", value=json.dumps(legacy, ensure_ascii=False))
    session.add(record)
    await session.commit()
    response = await client.get("/api/v1/friends/exchange-info")
    assert response.json() == legacy | {"rss_url": ""}
    assert json.loads(record.value) == legacy
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_admin=True)
    for value, expected in [("  https://feeds.example.com/rss.xml?a=1&b=2  ", "https://feeds.example.com/rss.xml?a=1&b=2"), ("  ", "")]:
        response = await client.put("/api/v1/friends/exchange-info", json=legacy | {"rss_url": value})
        assert response.status_code == 200
        assert response.json() == legacy | {"rss_url": expected}
        assert (await client.get("/api/v1/friends/exchange-info")).json() == response.json()
        assert json.loads(record.value) == response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["javascript:alert(1)", "data:text/plain,hello", "//example.com/rss", "/rss.xml", "https:example.com/rss", "https://", "https://example.com/a b", "https://example.com/" + "a" * 2048])
async def test_invalid_rss_config_is_rejected(rss_client, value):
    client, _, app = rss_client
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_admin=True)
    response = await client.put("/api/v1/friends/exchange-info", json={"rss_url": value})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_config_requires_admin_but_get_and_rss_are_public(rss_client):
    client, _, app = rss_client
    path = "/api/v1/friends/exchange-info"
    assert (await client.get(path)).status_code == 200
    assert (await client.get("/api/v1/rss.xml")).status_code == 200
    assert (await client.put(path, json={"rss_url": ""})).status_code == 401
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_admin=False)
    assert (await client.put(path, json={"rss_url": ""})).status_code == 403
