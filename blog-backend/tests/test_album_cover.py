"""相册封面更新的字段省略、显式清空、无效图片及首图回退回归。"""

from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.models.album import Album, AlbumPhoto
from app.models.image import UploadedImage
from tests.test_friend_snapshot import friend_env  # noqa: F401


@pytest_asyncio.fixture
async def album_env(friend_env):
    """仅使用独立临时数据库；图片记录不对应磁盘文件或真实对象存储。"""
    env = friend_env
    async with env.sessions() as db:
        db.add_all([
            UploadedImage(id=11, filename="first.jpg", original_name="first.jpg", url="/uploads/first.jpg"),
            UploadedImage(id=12, filename="second.jpg", original_name="second.jpg", url="/uploads/second.jpg"),
            UploadedImage(id=13, filename="cover.jpg", original_name="cover.jpg", url="/uploads/cover.jpg"),
        ])
        await db.flush()
        album = Album(title="测试相册", cover_image_id=13)
        db.add(album)
        await db.flush()
        db.add_all([
            AlbumPhoto(album_id=album.id, image_id=12, sort_order=2),
            AlbumPhoto(album_id=album.id, image_id=11, sort_order=1),
        ])
        await db.commit()
        album_id = album.id
    return SimpleNamespace(env=env, album_id=album_id, path=f"/api/v1/albums/{album_id}")


@pytest.mark.asyncio
async def test_omitted_cover_preserves_selected_image(album_env):
    case, env = album_env, album_env.env
    response = await env.client.put(case.path, headers=env.headers["admin"], json={"title": "已改标题"})
    assert response.status_code == 200
    detail = response.json()
    assert detail["title"] == "已改标题"
    assert detail["cover_image_id"] == 13
    assert detail["cover_url"] == "/uploads/cover.jpg"
    assert len(detail["photos"]) == 2


@pytest.mark.asyncio
async def test_null_cover_clears_selection_and_uses_first_photo_without_deleting_images(album_env):
    case, env = album_env, album_env.env
    response = await env.client.put(case.path, headers=env.headers["admin"], json={"cover_image_id": None})
    assert response.status_code == 200
    detail = response.json()
    assert detail["cover_image_id"] is None
    assert detail["cover_url"] == "/uploads/first.jpg"
    assert detail["photo_count"] == 2
    assert [photo["url"] for photo in detail["photos"]] == ["/uploads/first.jpg", "/uploads/second.jpg"]
    persisted = await env.client.get(case.path)
    assert persisted.json()["cover_image_id"] is None
    assert persisted.json()["cover_url"] == "/uploads/first.jpg"
    listing = await env.client.get("/api/v1/albums")
    assert listing.json()["items"][0]["cover_image_id"] is None
    assert listing.json()["items"][0]["cover_url"] == "/uploads/first.jpg"
    async with env.sessions() as db:
        assert await db.scalar(select(func.count(UploadedImage.id))) == 3
        assert await db.scalar(select(func.count(AlbumPhoto.id))) == 2


@pytest.mark.asyncio
async def test_invalid_cover_returns_detail_and_preserves_previous_album(album_env):
    case, env = album_env, album_env.env
    response = await env.client.put(
        case.path, headers=env.headers["admin"], json={"title": "不应保存", "cover_image_id": 999},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "图片 ID 999 不存在"
    persisted = (await env.client.get(case.path)).json()
    assert persisted["title"] == "测试相册"
    assert persisted["cover_image_id"] == 13
    assert persisted["cover_url"] == "/uploads/cover.jpg"


@pytest.mark.asyncio
async def test_valid_cover_can_be_changed_to_another_existing_image(album_env):
    case, env = album_env, album_env.env
    response = await env.client.put(case.path, headers=env.headers["admin"], json={"cover_image_id": 12})
    assert response.status_code == 200
    assert response.json()["cover_image_id"] == 12
    assert response.json()["cover_url"] == "/uploads/second.jpg"
