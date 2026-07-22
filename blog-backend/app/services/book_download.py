"""图书 ZIP 后台任务：磁盘生成、状态更新和过期清理。"""

import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.book import Book
from app.models.book_download import BookDownloadJob
from app.services.book import BOOKS_DIR


def normalize_utc(value: datetime | None) -> datetime | None:
    """将 SQLite 返回的 naive 时间按 UTC 解释并统一为 aware 时间。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def archive_path(job_id: int) -> Path:
    """根据任务 ID 解析当前环境中的归档路径，不信任历史绝对路径。"""
    return settings.BOOK_ARCHIVE_DIR / f"job-{job_id}.zip"


def existing_archive_path(job: BookDownloadJob) -> Path | None:
    """返回当前环境中存在的归档文件路径。"""
    path = archive_path(job.id)
    return path if path.is_file() else None


def _safe_name(book: Book) -> str:
    """生成 ZIP 内安全且可读的文件名。"""
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", f"{book.title} - {book.author}".strip(" -"))
    return f"{value or book.slug}.epub"


async def process_book_download_job(job_id: int) -> None:
    """在后台逐本写入临时 ZIP，并将进度持久化到任务表。"""
    async with AsyncSessionLocal() as db:
        job = await db.get(BookDownloadJob, job_id)
        if not job:
            return
        output_path = archive_path(job.id)
        output_path.unlink(missing_ok=True)
        job.output_path = ""
        job.file_size = 0
        job.error_message = ""
        job.completed_books = 0
        job.status = "running"
        await db.commit()

        try:
            slugs = json.loads(job.slugs_json)
            result = await db.execute(select(Book).where(Book.slug.in_(slugs)))
            book_map = {book.slug: book for book in result.scalars().all()}
            if len(book_map) != len(slugs):
                raise ValueError("部分图书不存在")

            settings.BOOK_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            used_names: set[str] = set()
            manifest: list[dict[str, str]] = []

            with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_STORED) as output:
                for index, slug in enumerate(slugs, start=1):
                    book = book_map[slug]
                    book_path = (BOOKS_DIR / f"{book.slug}.epub").resolve()
                    if not book_path.is_file() or BOOKS_DIR.resolve() not in book_path.parents:
                        raise FileNotFoundError(f"图书文件不存在：{book.title}")

                    filename = _safe_name(book)
                    stem, suffix = filename[:-5], filename[-5:]
                    candidate = filename
                    duplicate_index = 2
                    while candidate in used_names:
                        candidate = f"{stem} ({duplicate_index}){suffix}"
                        duplicate_index += 1
                    used_names.add(candidate)
                    output.write(book_path, f"books/{candidate}")
                    manifest.append({"slug": book.slug, "title": book.title, "author": book.author, "filename": candidate})

                    job.completed_books = index
                    await db.commit()

                output.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

            job.output_path = str(output_path)
            job.file_size = output_path.stat().st_size
            job.status = "completed"
            job.expires_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
                days=job.expire_days
            )
            await db.commit()
        except Exception as exc:
            output_path = locals().get("output_path")
            if isinstance(output_path, Path):
                output_path.unlink(missing_ok=True)
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            await db.commit()


async def cleanup_expired_book_archives() -> None:
    """按任务到期时间清理 ZIP，并删除没有对应任务的孤立文件。"""
    if not settings.BOOK_ARCHIVE_DIR.exists():
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(BookDownloadJob))
        jobs = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for job in jobs:
            expires_at = normalize_utc(job.expires_at)
            if expires_at and expires_at < now:
                archive_path(job.id).unlink(missing_ok=True)
                job.status = "expired" if job.status == "completed" else job.status
        await db.commit()

        active_paths = {
            archive_path(job.id).resolve()
            for job in jobs
            if job.status in {"pending", "running", "completed"}
        }
        for path in settings.BOOK_ARCHIVE_DIR.glob("job-*.zip"):
            if path.resolve() not in active_paths:
                # 孤立文件保留，避免清理任务误删尚未完成人工核对的归档。
                continue
