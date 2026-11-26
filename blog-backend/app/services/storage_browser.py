"""按目录合并本地文件与已登记的 R2 对象，不扫描存储桶或改动文件。"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models.background import Background
from app.models.book import Book
from app.models.book_download import BookDownloadJob
from app.models.file import UploadedFile
from app.models.gallery import GalleryProject
from app.models.image import UploadedImage
from app.models.post import Post
from app.models.post_download import PostDownloadJob
from app.schemas.storage import StorageBrowseResponse, StorageDirectory, StorageFile, StorageRoot


_DEFAULT_DIRS = {
    "uploads": ("images", "files", "books", "backgrounds", "book-archives", "post-archives"),
    "content": ("posts", "gallery"),
}


def _valid_path(path: str) -> bool:
    """数据库键和请求路径共用校验，拒绝绝对路径、隐藏目录和路径穿越。"""
    return not path or (
        not any(ord(char) < 32 or char in "\\:\x7f" for char in path)
        and all(part and part not in (".", "..") and not part.startswith(".") for part in path.split("/"))
    )


def _local_path(base: Path, path: str) -> Path:
    """限制在指定根目录内，同时拒绝沿符号链接访问其他位置。"""
    if not _valid_path(path):
        raise HTTPException(status_code=400, detail="目录路径无效")
    candidate = base
    for part in path.split("/") if path else ():
        candidate = candidate / part
        if candidate.is_symlink():
            raise HTTPException(status_code=400, detail="不支持符号链接目录")
    try:
        candidate.resolve().relative_to(base.resolve())
    except (ValueError, OSError, RuntimeError):
        raise HTTPException(status_code=400, detail="目录路径无效")
    return candidate


def _scan_local(base: Path, path: str) -> tuple[bool, list[StorageDirectory], dict[str, StorageFile]]:
    """只扫描当前层级，文件系统操作在线程池运行，不递归遍历大目录。"""
    directory = _local_path(base, path)
    if directory.exists() and not directory.is_dir():
        raise HTTPException(status_code=400, detail="该路径不是目录")
    folders: list[StorageDirectory] = []
    files: dict[str, StorageFile] = {}
    if not directory.is_dir():
        return False, folders, files
    try:
        for child in directory.iterdir():
            relative = f"{path}/{child.name}" if path else child.name
            if not _valid_path(relative) or child.is_symlink():
                continue
            try:
                if child.is_dir():
                    folders.append(StorageDirectory(name=child.name, path=relative))
                elif child.is_file():
                    stat = child.stat()
                    files[relative] = StorageFile(
                        name=child.name, path=relative, file_size=stat.st_size,
                        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc), local_exists=True,
                    )
            except FileNotFoundError:
                # 文件可能在浏览期间被正常删除，下一次刷新会反映新状态。
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="没有读取该目录的权限")
    return True, folders, files


def _record(path: str, kind: str, row_id: int, title: str, created_at: datetime,
            manage_url: str, *, size: int | None = None, storage: str = "local",
            r2_key: str | None = None, url: str | None = None) -> StorageFile:
    """将不同业务表的元数据收敛成统一条目，R2 域名仍从配置派生。"""
    r2_url = None
    if storage == "r2" and r2_key and settings.R2_PUBLIC_DOMAIN:
        r2_url = f"{settings.R2_PUBLIC_DOMAIN.rstrip('/')}/{quote(r2_key, safe='/')}"
    return StorageFile(
        name=path.rsplit("/", 1)[-1], path=path, title=title, file_size=size,
        modified_at=created_at, storage_backend="r2" if storage == "r2" else "local",
        record_kind=kind, record_id=row_id, r2_key=r2_key, r2_url=r2_url, url=url,
        manage_url=manage_url,
    )


async def _upload_records(db: AsyncSession, path: str) -> list[StorageFile]:
    """查询当前子树的上传记录，只取元数据列，不加载正文或远程对象。"""
    records: list[StorageFile] = []
    prefix = f"{path}/" if path else ""
    for model, kind, tab in ((UploadedImage, "image", "images"), (UploadedFile, "file", "files")):
        rows = await db.execute(select(
            model.id, model.filename, model.original_name, model.created_at,
            model.file_size, model.storage_backend, model.r2_key, model.url,
        ).where(model.filename.startswith(prefix, autoescape=True)))
        for row in rows:
            records.append(_record(
                row.filename, kind, row.id, row.original_name, row.created_at,
                f"/admin/files?view=library&tab={tab}", size=row.file_size,
                storage=row.storage_backend, r2_key=row.r2_key, url=row.url,
            ))

    if not path or path == "books" or path.startswith("books/"):
        rows = await db.execute(select(Book.id, Book.slug, Book.title, Book.created_at,
                                       Book.storage_backend, Book.r2_key))
        for row in rows:
            records.append(_record(
                f"books/{row.slug}.epub", "book", row.id, row.title, row.created_at, "/admin/books",
                storage=row.storage_backend, r2_key=row.r2_key,
                url=f"/api/v1/books/{quote(row.slug, safe='')}/read",
            ))
    if not path or path == "backgrounds" or path.startswith("backgrounds/"):
        rows = await db.execute(select(Background.id, Background.media_url, Background.created_at,
                                       Background.storage_backend, Background.r2_key, Background.file_size)
                                .where(Background.media_type == "video"))
        for row in rows:
            for media_prefix in ("/uploads/backgrounds/", "/api/v1/backgrounds/media/"):
                if row.media_url.startswith(media_prefix):
                    name = row.media_url.removeprefix(media_prefix)
                    records.append(_record(
                        f"backgrounds/{name}", "background", row.id, name, row.created_at,
                        "/admin/backgrounds", size=row.file_size, storage=row.storage_backend,
                        r2_key=row.r2_key, url=row.media_url,
                    ))
                    break
    for model, kind, directory, manage_url in (
        (BookDownloadJob, "book_archive", "book-archives", "/admin/files?view=library&tab=archives"),
        (PostDownloadJob, "post_archive", "post-archives", "/admin/posts"),
    ):
        if path and path != directory and not path.startswith(f"{directory}/"):
            continue
        rows = await db.execute(select(model.id, model.output_path, model.archive_name,
                                       model.created_at, model.file_size))
        for row in rows:
            if row.output_path:
                name = row.output_path.replace("\\", "/").rsplit("/", 1)[-1]
                records.append(_record(f"{directory}/{name}", kind, row.id, row.archive_name,
                                       row.created_at, manage_url, size=row.file_size))
    return records


async def _content_records(db: AsyncSession, path: str) -> list[StorageFile]:
    """关联 Markdown 原文件；不读取数据库中的文章 HTML。"""
    records: list[StorageFile] = []
    for model, kind, directory, manage_url in (
        (Post, "post", "posts", "/admin/posts"),
        (GalleryProject, "gallery", "gallery", "/admin/gallery"),
    ):
        if path and path != directory and not path.startswith(f"{directory}/"):
            continue
        rows = await db.execute(select(model.id, model.md_filename, model.title, model.created_at))
        for row in rows:
            if row.md_filename:
                records.append(_record(f"{directory}/{row.md_filename}", kind, row.id, row.title,
                                       row.created_at, manage_url))
    return records


async def browse_storage(db: AsyncSession, root: StorageRoot, path: str,
                         page: int = 1, page_size: int = 100) -> StorageBrowseResponse:
    """浏览授权根目录，合并本地副本、R2 记录和缺失文件，目录不受文件分页影响。"""
    base = settings.UPLOAD_DIR if root == "uploads" else settings.CONTENT_DIR
    exists, folders, files = await run_in_threadpool(_scan_local, base, path)
    records = await (_upload_records(db, path) if root == "uploads" else _content_records(db, path))
    directory_map = {folder.path: folder for folder in folders}
    prefix = f"{path}/" if path else ""
    if not path:
        for name in _DEFAULT_DIRS[root]:
            # 预置业务目录即使暂未生成本地文件，也能作为空目录浏览。
            if not (base / name).is_symlink():
                directory_map.setdefault(name, StorageDirectory(name=name, path=name))
    has_record = False
    for record in records:
        if not _valid_path(record.path) or not record.path.startswith(prefix):
            continue
        try:
            _local_path(base, record.path)
        except HTTPException:
            continue
        tail = record.path.removeprefix(prefix)
        if "/" in tail:
            name = tail.split("/", 1)[0]
            child_path = f"{prefix}{name}"
            directory_map.setdefault(child_path, StorageDirectory(name=name, path=child_path))
        elif tail:
            local = files.get(record.path)
            if local:
                record.local_exists = True
                record.file_size = local.file_size
                record.modified_at = local.modified_at
            files[record.path] = record
        has_record = True
    if path and not exists and not has_record and path not in _DEFAULT_DIRS[root]:
        raise HTTPException(status_code=404, detail="目录不存在")
    all_files = sorted(files.values(), key=lambda item: (item.name.casefold(), item.name))
    start = (page - 1) * page_size
    return StorageBrowseResponse(
        root=root, path=path, directories=sorted(directory_map.values(), key=lambda item: item.name.casefold()),
        items=all_files[start:start + page_size], total=len(all_files), page=page, page_size=page_size,
        r2_enabled=settings.R2_ENABLED,
    )
