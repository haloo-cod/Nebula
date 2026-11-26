"""上传路径的真实 HTTP 访问和本地文件边界回归。"""

from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio

from app.config import settings
from app.database import get_db
from app.models.file import UploadedFile
from app.models.image import UploadedImage
from app.models.background import Background
from app.services import file as file_service, image as image_service
from tests.test_friend_snapshot import friend_env  # noqa: F401


@pytest_asyncio.fixture
async def upload_env(friend_env, tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(settings, "R2_ENABLED", False)
    settings.UPLOAD_DIR.mkdir()
    monkeypatch.setattr(main, "AsyncSessionLocal", friend_env.sessions)
    monkeypatch.setitem(main.app.dependency_overrides, get_db, friend_env.app.dependency_overrides[get_db])
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app, raise_app_exceptions=False), base_url="http://test",
    ) as client:
        yield SimpleNamespace(client=client, sessions=friend_env.sessions, headers=friend_env.headers, root=settings.UPLOAD_DIR)


@pytest.mark.asyncio
async def test_download_confines_to_upload_dir(upload_env):
    env = upload_env
    marker = env.root.parent / "marker.txt"
    marker.write_text("outside uploads", encoding="utf-8")
    async with env.sessions() as db:
        record = UploadedFile(filename="../marker.txt", original_name="marker.txt")
        db.add(record)
        await db.commit()
        file_id = record.id
    response = await env.client.get(f"/api/v1/files/{file_id}/download")
    assert response.status_code == 404 and response.json()["detail"] == "文件不存在"
    deleted = await env.client.delete(f"/api/v1/files/{file_id}", headers=env.headers["admin"])
    assert deleted.status_code == 500
    assert marker.read_text("utf-8") == "outside uploads"
    async with env.sessions() as db:
        assert await db.get(UploadedFile, file_id) is not None
    safe = env.root / "files" / "safe.txt"
    safe.parent.mkdir()
    safe.write_text("safe download", encoding="utf-8")
    async with env.sessions() as db:
        record = UploadedFile(filename="files/safe.txt", original_name="safe.txt")
        db.add(record)
        await db.commit()
        safe_id = record.id
    downloaded = await env.client.get(f"/api/v1/files/{safe_id}/download")
    assert downloaded.status_code == 200 and downloaded.text == "safe download"
    assert (await env.client.delete(f"/api/v1/files/{safe_id}", headers=env.headers["admin"])).status_code == 204
    assert not safe.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["fallback", "image", "file", "background"])
async def test_serve_upload_fallback_confined(upload_env, kind):
    env = upload_env
    marker = env.root.parent / "marker.txt"
    marker.write_text("private marker", encoding="utf-8")
    prefix = {"image": "images", "file": "files", "background": "backgrounds"}.get(kind, "images")
    filename = f"{prefix}/../../marker.txt"
    async with env.sessions() as db:
        if kind == "image":
            db.add(UploadedImage(filename=filename, original_name="marker.txt", url=f"/uploads/{filename}"))
        elif kind == "file":
            db.add(UploadedFile(filename=filename, original_name="marker.txt"))
        elif kind == "background":
            db.add(Background(theme="dark", device="desktop", media_type="video", media_url=f"/uploads/{filename}"))
        await db.commit()
    response = await env.client.get(f"/uploads/{prefix}/%2e%2e/%2e%2e/marker.txt")
    assert response.status_code == 404 and response.json()["detail"] == "文件不存在"
    assert marker.read_text("utf-8") == "private marker"
    safe = env.root / "safe.txt"
    safe.write_text("safe fallback", encoding="utf-8")
    downloaded = await env.client.get("/uploads/safe.txt")
    assert downloaded.status_code == 200 and downloaded.text == "safe fallback"


@pytest.mark.parametrize("service", [file_service, image_service])
@pytest.mark.parametrize("relative", ["../marker.txt", "images/../../marker.txt", "", "files//marker.txt"])
def test_local_helpers_reject_unsafe_paths(tmp_path, monkeypatch, service, relative):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "uploads")
    settings.UPLOAD_DIR.mkdir()
    marker = tmp_path / "marker.txt"
    marker.write_text("keep", encoding="utf-8")
    for unsafe in (relative, str(marker.resolve())):
        with pytest.raises(ValueError, match="上传文件路径越界"):
            service.resolve_upload_path(unsafe)
        with pytest.raises(ValueError, match="上传文件路径越界"):
            service.delete_file(unsafe)
    assert marker.read_text("utf-8") == "keep"


@pytest.mark.asyncio
async def test_register_upload_rejects_traversal_key(upload_env, monkeypatch):
    from app.api.v1 import r2_migration

    checked = []

    def missing_object(key):
        checked.append(key)
        return False

    monkeypatch.setattr(r2_migration, "_require_r2", lambda: SimpleNamespace(file_exists=missing_object))
    url = "/api/v1/r2-migration/register-upload"
    for directory, key in [
        ("files", "files/../../../../etc/marker"),
        ("files", "files/../x.txt"),
        ("files", "files/" + "a" * 32 + ".txt\n"),
        ("images", "images/2026/10/abcdef123456_../../marker.png"),
        ("images", "files/" + "a" * 32 + ".png"),
    ]:
        response = await upload_env.client.post(url, headers=upload_env.headers["admin"], json={
            "directory": directory, "r2_key": key, "original_name": "marker.txt",
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "r2_key 格式不合法，仅接受 presign-upload 生成的对象键"
    assert checked == []
    valid_key = "files/" + "a" * 32 + ".txt"
    response = await upload_env.client.post(url, headers=upload_env.headers["admin"], json={
        "directory": "files", "r2_key": valid_key, "original_name": "marker.txt",
    })
    assert response.status_code == 400 and response.json()["detail"] == "对象尚未上传到 R2，请先完成直传"
    assert checked == [valid_key]


@pytest.mark.asyncio
@pytest.mark.parametrize("directory,filename", [
    ("images", "照片 空格.PNG"), ("images", "x" * 250 + ".png"),
    ("images", ".png"), ("images", "a.b-c_d.png"), ("files", "资料.ZIP"),
])
async def test_presigned_keys_can_be_registered(upload_env, monkeypatch, directory, filename):
    from app.api.v1 import r2_migration

    monkeypatch.setattr(settings, "R2_ENABLED", True)
    monkeypatch.setattr(r2_migration, "_require_r2", lambda: SimpleNamespace(
        presign_put=lambda key, **kwargs: f"https://r2.test/{key}", file_exists=lambda key: True,
    ))
    signed = await upload_env.client.post("/api/v1/r2-migration/presign-upload", headers=upload_env.headers["admin"],
        json={"directory": directory, "filename": filename})
    if filename == ".png":
        assert signed.status_code == 400
        return
    assert signed.status_code == 200
    response = await upload_env.client.post("/api/v1/r2-migration/register-upload", headers=upload_env.headers["admin"],
        json={"directory": directory, "r2_key": signed.json()["r2_key"], "original_name": filename})
    assert response.status_code == 201 and response.json()["original_name"] == filename
