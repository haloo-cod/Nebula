"""背景来源 API：完整数据流、权限、校验及身份保持。"""

from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.api.v1.backgrounds import router
from app.database import get_db
from app.models import Base
from app.models.image import UploadedImage


@pytest_asyncio.fixture
async def source_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        image = UploadedImage(filename="source-test.png", original_name="source-test.png", url="/uploads/source-test.png")
        session.add(image)
        await session.commit()
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def test_db():
            yield session

        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_admin=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            yield client, app, image.id
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("media", ["uploaded-image", "external-image", "video"])
async def test_source_round_trip_and_clear(source_client, media):
    client, _, image_id = source_client
    payload = {"theme": "dark", "device": "desktop", "sort_order": 7,
               "source_text": "  画师 · 测试作品  ", "source_url": "  https://example.com/work?a=1  "}
    if media == "uploaded-image":
        payload["image_id"] = image_id
    else:
        payload.update(media_type="video" if media == "video" else "image",
                       media_url="https://example.com/background.mp4" if media == "video" else "https://example.com/image.png")
    created = await client.post("/api/v1/backgrounds", json=payload)
    assert created.status_code == 201
    row = created.json()
    assert row["source_text"] == "画师 · 测试作品"
    assert row["source_url"] == "https://example.com/work?a=1"
    updated = await client.patch(f"/api/v1/backgrounds/{row['id']}/source",
                                 json={"source_text": "另一条来源", "source_url": ""})
    assert updated.status_code == 200
    assert updated.json()["id"] == row["id"]
    assert updated.json()["url"] == row["url"]
    assert updated.json()["sort_order"] == 7
    listed = (await client.get("/api/v1/backgrounds?theme=dark&device=desktop")).json()["items"]
    assert listed[0]["source_text"] == "另一条来源"
    cleared = await client.patch(f"/api/v1/backgrounds/{row['id']}/source",
                                json={"source_text": "", "source_url": ""})
    assert cleared.json()["source_text"] == cleared.json()["source_url"] == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["javascript:alert(1)", "//example.com", "https:example.com", "http://", "https://example.com/a b"])
async def test_invalid_source_urls(source_client, url):
    client, _, image_id = source_client
    payload = {"theme": "dark", "device": "desktop", "image_id": image_id,
               "source_text": "来源", "source_url": url}
    assert (await client.post("/api/v1/backgrounds", json=payload)).status_code == 422
    assert (await client.patch("/api/v1/backgrounds/1/source", json={"source_text": "", "source_url": url})).status_code == 422


@pytest.mark.asyncio
async def test_source_permissions_missing_and_lengths(source_client):
    client, app, _ = source_client
    path = "/api/v1/backgrounds/999/source"
    source = {"source_text": "来源", "source_url": "https://example.com"}
    assert (await client.patch(path, json=source)).status_code == 404
    assert (await client.patch(path, json={**source, "source_text": "字" * 121})).status_code == 422
    assert (await client.patch(path, json={**source, "source_url": "https://example.com/" + "a" * 2048})).status_code == 422
    assert (await client.patch(path, json={"source_text": ""})).status_code == 422
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_admin=False)
    assert (await client.patch(path, json=source)).status_code == 403
    del app.dependency_overrides[get_current_user]
    assert (await client.patch(path, json=source)).status_code == 401


@pytest.mark.asyncio
async def test_reorder_keeps_sources_with_background_ids(source_client):
    client, _, image_id = source_client
    rows = []
    for text in ["画师甲", "画师乙"]:
        rows.append((await client.post("/api/v1/backgrounds", json={
            "theme": "dark", "device": "desktop", "image_id": image_id, "source_text": text,
        })).json())
    response = await client.put("/api/v1/backgrounds/reorder", json={
        "ids": [row["id"] for row in reversed(rows)], "theme": "dark", "device": "desktop",
    })
    assert response.status_code == 204
    items = (await client.get("/api/v1/backgrounds")).json()["items"]
    assert [(row["id"], row["source_text"]) for row in items] == [(row["id"], row["source_text"]) for row in reversed(rows)]
