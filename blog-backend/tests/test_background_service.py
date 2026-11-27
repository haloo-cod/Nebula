"""Background media-source validation and end-to-end API tests."""

from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.api.v1.backgrounds import router
from app.config import settings
from app.database import get_db
from app.models import Base
from app.models.background import Background
from app.services.background import create_background
from app.services import r2_storage


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def bg_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    (tmp_path / "backgrounds").mkdir(parents=True, exist_ok=True)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def test_db():
            yield session

        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(is_admin=True)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            follow_redirects=False,
        ) as client:
            yield client, session, tmp_path
    await engine.dispose()


@pytest.mark.asyncio
async def test_video_background_accepts_null_image_id(db_session):
    result = await create_background(
        db_session,
        image_id=None,
        theme="dark",
        device="desktop",
        media_type="video",
        media_url="/api/v1/files/1/media",
        mime_type="video/mp4",
        file_size=1,
    )
    assert result["media_type"] == "video"
    assert result["url"] == "/api/v1/files/1/media"
    assert result["storage_backend"] == "local"


@pytest.mark.asyncio
async def test_image_background_still_requires_a_source(db_session):
    with pytest.raises(ValueError, match="image background requires"):
        await create_background(
            db_session,
            image_id=None,
            theme="light",
            device="desktop",
            media_type="image",
        )


@pytest.mark.asyncio
async def test_r2_video_upload_persists_storage_backend_and_redirects_with_query(
    bg_api_client, monkeypatch
):
    client, session, tmp_path = bg_api_client
    uploaded_keys: list[str] = []

    class FakeR2:
        def upload_local_file(self, key, local_path, content_type=None):
            uploaded_keys.append(key)
            assert local_path.is_file()
            assert content_type == "video/mp4"

        def get_public_url(self, key: str) -> str:
            return f"https://r2.example.com/{key}"

    monkeypatch.setattr(settings, "R2_ENABLED", True)
    monkeypatch.setattr(settings, "R2_PUBLIC_DOMAIN", "https://r2.example.com")
    monkeypatch.setattr(r2_storage, "get_r2_client", lambda: FakeR2())

    upload_resp = await client.post(
        "/api/v1/backgrounds/video-upload?storage_backend=r2",
        files={"file": ("clip.mp4", b"fake-mp4-bytes", "video/mp4")},
    )
    assert upload_resp.status_code == 200
    uploaded = upload_resp.json()
    assert uploaded["storage_backend"] == "r2"
    assert len(uploaded_keys) == 1
    assert "\\" not in uploaded_keys[0]
    assert uploaded_keys[0].startswith("backgrounds/")

    create_resp = await client.post(
        "/api/v1/backgrounds",
        json={
            "theme": "dark",
            "device": "desktop",
            "media_type": "video",
            "media_url": uploaded["url"],
            "mime_type": uploaded["mime_type"],
            "file_size": uploaded["file_size"],
            "storage_backend": uploaded["storage_backend"],
            "source_text": "画师R2",
            "source_url": "https://example.com/r2",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["storage_backend"] == "r2"

    row = (await session.execute(select(Background).where(Background.id == created["id"]))).scalar_one()
    assert row.storage_backend == "r2"
    assert row.r2_key == uploaded_keys[0]

    media_resp = await client.get(f"{uploaded['url']}?_cors=2&video=full")
    assert media_resp.status_code == 307
    assert media_resp.headers["location"] == f"https://r2.example.com/{uploaded_keys[0]}?_cors=2&video=full"

    # 多条背景记录复用同一视频 URL 时，媒体接口仍返回 307（不触发 MultipleResultsFound 500）
    second_resp = await client.post(
        "/api/v1/backgrounds",
        json={
            "theme": "light",
            "device": "desktop",
            "media_type": "video",
            "media_url": uploaded["url"],
            "mime_type": uploaded["mime_type"],
            "file_size": uploaded["file_size"],
            "storage_backend": uploaded["storage_backend"],
        },
    )
    assert second_resp.status_code == 201
    second_id = second_resp.json()["id"]
    shared_media_resp = await client.get(f"{uploaded['url']}?_cors=2")
    assert shared_media_resp.status_code == 307
    assert shared_media_resp.headers["location"] == f"https://r2.example.com/{uploaded_keys[0]}?_cors=2"

    # 删除其中一条引用时应保留本地副本；删除最后一条引用后清理本地副本
    filename = uploaded["url"].rsplit("/", 1)[-1]
    assert (tmp_path / "backgrounds" / filename).is_file()
    assert (await client.delete(f"/api/v1/backgrounds/{second_id}")).status_code == 204
    assert (tmp_path / "backgrounds" / filename).is_file()
    delete_resp = await client.delete(f"/api/v1/backgrounds/{created['id']}")
    assert delete_resp.status_code == 204
    assert not (tmp_path / "backgrounds" / filename).exists()


@pytest.mark.asyncio
async def test_r2_storage_backend_rejected_for_non_local_or_disabled_r2(bg_api_client, monkeypatch):
    client, _, _ = bg_api_client
    monkeypatch.setattr(settings, "R2_ENABLED", False)
    disabled_resp = await client.post(
        "/api/v1/backgrounds",
        json={
            "theme": "dark",
            "device": "desktop",
            "media_type": "video",
            "media_url": "/api/v1/backgrounds/media/a.mp4",
            "storage_backend": "r2",
        },
    )
    assert disabled_resp.status_code == 400

    monkeypatch.setattr(settings, "R2_ENABLED", True)
    external_resp = await client.post(
        "/api/v1/backgrounds",
        json={
            "theme": "dark",
            "device": "desktop",
            "media_type": "video",
            "media_url": "https://cdn.example.com/a.mp4",
            "storage_backend": "r2",
        },
    )
    assert external_resp.status_code == 400
