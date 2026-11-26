"""图片的分页搜索与正在使用图片的删除保护。"""

import pytest

from app.config import settings
from app.models.background import Background
from app.models.image import UploadedImage
from app.models.post import Post
from tests.test_friend_snapshot import friend_env  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize("reference", ["post", "background", "poster"])
async def test_url_image_reference_blocks_delete_and_release_allows_it(friend_env, monkeypatch, tmp_path, reference):
    env = friend_env
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(settings, "R2_ENABLED", False)
    path = settings.UPLOAD_DIR / "images" / "safe.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"image must survive rejected deletion")
    url = "/uploads/images/safe.png"
    async with env.sessions() as db:
        image = UploadedImage(filename="images/safe.png", original_name="safe.png", url=url)
        db.add(image)
        await db.flush()
        image_id = image.id
        if reference == "post":
            owner = Post(slug="protected-image", title="Protected", date="2026-10-26", cover_url=url)
        elif reference == "background":
            owner = Background(media_type="image", image_id=None, media_url=url, theme="dark", device="desktop")
        else:
            owner = Background(media_type="video", image_id=None, media_url="https://example.com/video.mp4", poster_url=url,
                               theme="dark", device="desktop")
        db.add(owner)
        await db.commit()
        owner_id = owner.id

    rejected = await env.client.delete(f"/api/v1/images/{image_id}", headers=env.headers["admin"])
    assert rejected.status_code == 409
    assert path.read_bytes() == b"image must survive rejected deletion"
    async with env.sessions() as db:
        assert await db.get(UploadedImage, image_id) is not None
        owner = await db.get(Post if reference == "post" else Background, owner_id)
        await db.delete(owner)
        await db.commit()
    removed = await env.client.delete(f"/api/v1/images/{image_id}", headers=env.headers["admin"])
    assert removed.status_code == 204
    assert not path.exists()
    async with env.sessions() as db:
        assert await db.get(UploadedImage, image_id) is None


@pytest.mark.asyncio
async def test_image_search_finds_old_records_outside_first_page_and_escapes_wildcards(friend_env):
    env = friend_env
    async with env.sessions() as db:
        for index in range(105):
            db.add(UploadedImage(
                id=index + 1, filename=f"images/photo-{index}.png",
                original_name="needle%photo.png" if index == 0 else f"photo-{index}.png",
                url=f"/uploads/images/photo-{index}.png",
            ))
        await db.commit()
    first = await env.client.get("/api/v1/images", params={"page": 1, "page_size": 100}, headers=env.headers["admin"])
    second = await env.client.get("/api/v1/images", params={"page": 2, "page_size": 100}, headers=env.headers["admin"])
    assert first.status_code == second.status_code == 200
    first_ids = {item["id"] for item in first.json()["items"]}
    second_ids = {item["id"] for item in second.json()["items"]}
    assert first_ids.isdisjoint(second_ids)
    assert first_ids | second_ids == set(range(1, 106))
    assert first.json()["total"] == second.json()["total"] == 105
    found = await env.client.get("/api/v1/images", params={"keyword": "NEEDLE%", "page_size": 20}, headers=env.headers["admin"])
    assert found.status_code == 200
    assert found.json()["total"] == 1
    assert [item["id"] for item in found.json()["items"]] == [1]
    literal = await env.client.get("/api/v1/images", params={"keyword": "%"}, headers=env.headers["admin"])
    assert literal.json()["total"] == 1
