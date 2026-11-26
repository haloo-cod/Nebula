"""目录浏览的权限、路径边界、本地 / R2 合并及业务文件关联。"""

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.api.v1.storage import router
from app.config import settings
from app.database import get_db
from app.models import Base
from app.models.background import Background
from app.models.book import Book
from app.models.book_download import BookDownloadJob
from app.models.file import UploadedFile
from app.models.gallery import GalleryProject
from app.models.image import UploadedImage
from app.models.post import Post
from app.models.post_download import PostDownloadJob


@pytest_asyncio.fixture
async def storage_client(tmp_path, monkeypatch):
    """使用临时文件夹和内存数据库，任何测试都不访问真实 R2。"""
    uploads, content = tmp_path / "uploads", tmp_path / "content"
    uploads.mkdir()
    content.mkdir()
    monkeypatch.setattr(settings, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(settings, "CONTENT_DIR", content)
    monkeypatch.setattr(settings, "R2_ENABLED", True)
    monkeypatch.setattr(settings, "R2_PUBLIC_DOMAIN", "https://r2.example.com")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            app = FastAPI()
            app.include_router(router, prefix="/api/v1")

            async def test_db():
                yield db

            app.dependency_overrides[get_db] = test_db
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, is_admin=True)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                yield client, db, app, uploads, content
    finally:
        await engine.dispose()


def put_file(root: Path, path: str, content: bytes = b"local"):
    """创建独立测试文件并返回路径。"""
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


@pytest.mark.asyncio
async def test_roots_folders_and_read_only_local_files(storage_client):
    client, _, _, uploads, _ = storage_client
    sample = put_file(uploads, "custom/中文.txt", b"unchanged")
    put_file(uploads, ".hidden/secret.txt")
    response = await client.get("/api/v1/storage/browse")
    assert response.status_code == 200
    folders = {item["path"] for item in response.json()["directories"]}
    assert {"images", "files", "books", "backgrounds", "book-archives", "post-archives", "custom"} <= folders
    assert ".hidden" not in folders
    result = (await client.get("/api/v1/storage/browse", params={"path": "custom"})).json()
    item = result["items"][0]
    assert item["name"] == "中文.txt" and item["path"] == "custom/中文.txt"
    assert item["local_exists"] and item["storage_backend"] == "local" and item["record_id"] is None
    assert item["file_size"] == 9 and sample.read_bytes() == b"unchanged"
    assert str(uploads) not in response.text


@pytest.mark.asyncio
async def test_remote_only_images_nested_folders_and_local_copy_merge(storage_client):
    client, db, _, uploads, _ = storage_client
    local = put_file(uploads, "images/2026/10/中文 #%.png", b"same-file")
    db.add_all([
        UploadedImage(filename="images/2026/10/中文 #%.png", original_name="原始名字.png",
                      url="/uploads/images/2026/10/中文 #%.png", storage_backend="r2",
                      r2_key="images/2026/10/中文 #?.png", file_size=9),
        UploadedImage(filename="images/2026/11/remote.png", original_name="remote.png",
                      url="/uploads/images/2026/11/remote.png", storage_backend="r2",
                      r2_key="images/2026/11/remote.png", file_size=25),
    ])
    await db.commit()
    result = (await client.get("/api/v1/storage/browse", params={"path": "images/2026"})).json()
    assert [item["name"] for item in result["directories"]] == ["10", "11"]
    result = (await client.get("/api/v1/storage/browse", params={"path": "images/2026/10"})).json()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["storage_backend"] == "r2" and item["local_exists"] and item["record_kind"] == "image"
    assert item["title"] == "原始名字.png"
    assert item["r2_url"] == "https://r2.example.com/images/2026/10/%E4%B8%AD%E6%96%87%20%23%3F.png"
    remote = (await client.get("/api/v1/storage/browse", params={"path": "images/2026/11"})).json()["items"][0]
    assert remote["storage_backend"] == "r2" and not remote["local_exists"] and remote["file_size"] == 25
    assert local.read_bytes() == b"same-file"


@pytest.mark.asyncio
async def test_files_missing_records_and_pagination(storage_client):
    client, db, _, uploads, _ = storage_client
    put_file(uploads, "files/unregistered.zip")
    db.add_all([
        UploadedFile(filename="files/missing.zip", original_name="missing.zip", file_size=2),
        UploadedFile(filename="files/remote.zip", original_name="remote.zip", storage_backend="r2", r2_key="files/remote.zip"),
    ])
    await db.commit()
    first = (await client.get("/api/v1/storage/browse", params={"path": "files", "page_size": 2})).json()
    second = (await client.get("/api/v1/storage/browse", params={"path": "files", "page_size": 2, "page": 2})).json()
    assert first["total"] == second["total"] == 3
    assert [item["name"] for item in first["items"] + second["items"]] == ["missing.zip", "remote.zip", "unregistered.zip"]
    assert not first["items"][0]["local_exists"] and first["items"][0]["storage_backend"] == "local"


@pytest.mark.asyncio
async def test_books_backgrounds_archives_and_content_associations(storage_client):
    client, db, _, uploads, content = storage_client
    put_file(uploads, "books/中文书.epub")
    put_file(content, "posts/博文.md")
    put_file(content, "gallery/展览.md")
    db.add_all([
        Book(slug="中文书", title="书名", storage_backend="r2", r2_key="books/中文书.epub"),
        Background(media_type="video", media_url="/api/v1/backgrounds/media/clip.mp4", theme="light", device="desktop",
                   storage_backend="r2", r2_key="backgrounds/clip.mp4"),
        Background(media_type="video", media_url="/api/v1/files/10/media", theme="dark", device="desktop"),
        BookDownloadJob(user_id=1, slugs_json="[]", archive_name="图书导出", output_path="/old/server/uploads/book-archives/job-1.zip"),
        PostDownloadJob(user_id=1, slugs_json="[]", archive_name="文章导出", output_path="C:\\old\\uploads\\post-archives\\job-2.zip"),
        Post(slug="post", title="博文标题", md_filename="博文.md", content_html="不应返回的正文"),
        GalleryProject(slug="gallery", title="展览标题", md_filename="展览.md"),
    ])
    await db.commit()
    expected = {"books": "book", "backgrounds": "background", "book-archives": "book_archive", "post-archives": "post_archive"}
    for path, kind in expected.items():
        result = (await client.get("/api/v1/storage/browse", params={"path": path})).json()
        assert result["total"] == 1 and result["items"][0]["record_kind"] == kind
    for path, kind in (("posts", "post"), ("gallery", "gallery")):
        response = await client.get("/api/v1/storage/browse", params={"root": "content", "path": path})
        assert response.json()["items"][0]["record_kind"] == kind
        assert "不应返回的正文" not in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["..", "../outside", "/etc", "images/../../", "images\\..\\", "C:/Windows", ".env", "images/.secret", "images//x", "images/./x", "bad\x00name"])
async def test_invalid_paths_are_rejected(storage_client, path):
    client, _, _, _, _ = storage_client
    response = await client.get("/api/v1/storage/browse", params={"path": path})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_symlinks_and_poisoned_database_paths_cannot_escape(storage_client, tmp_path):
    client, db, _, uploads, _ = storage_client
    outside = tmp_path / "outside"
    outside.mkdir()
    put_file(outside, "private.txt")
    try:
        (uploads / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("当前 Windows 账户无创建符号链接权限")
    db.add(UploadedFile(filename="link/private.txt", original_name="private.txt"))
    await db.commit()
    response = await client.get("/api/v1/storage/browse")
    assert "link" not in {item["name"] for item in response.json()["directories"]}
    assert (await client.get("/api/v1/storage/browse", params={"path": "link"})).status_code == 400


@pytest.mark.asyncio
async def test_admin_permission_validation_and_r2_disabled(storage_client, monkeypatch):
    client, _, app, _, _ = storage_client
    monkeypatch.setattr(settings, "R2_ENABLED", False)
    assert (await client.get("/api/v1/storage/browse")).json()["r2_enabled"] is False
    for params in ({"root": "data"}, {"page": 0}, {"page_size": 201}):
        assert (await client.get("/api/v1/storage/browse", params=params)).status_code == 422
    assert (await client.get("/api/v1/storage/browse", params={"path": "not-found"})).status_code == 404
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2, is_admin=False)
    assert (await client.get("/api/v1/storage/browse")).status_code == 403
    app.dependency_overrides.clear()
    assert (await client.get("/api/v1/storage/browse")).status_code == 401


@pytest.mark.asyncio
async def test_poisoned_record_paths_and_file_as_directory_are_rejected(storage_client):
    client, db, _, uploads, _ = storage_client
    put_file(uploads, "files/not-a-directory")
    db.add_all([
        UploadedFile(filename="../outside/private.txt", original_name="secret"),
        UploadedFile(filename="/etc/passwd", original_name="secret"),
        UploadedFile(filename=".hidden/secret", original_name="secret"),
    ])
    await db.commit()
    result = (await client.get("/api/v1/storage/browse")).json()
    assert not result["items"]
    assert "outside" not in {item["name"] for item in result["directories"]}
    assert (await client.get("/api/v1/storage/browse", params={"path": "files/not-a-directory"})).status_code == 400
