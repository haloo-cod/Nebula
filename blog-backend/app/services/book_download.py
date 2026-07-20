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
        archive_path = settings.BOOK_ARCHIVE_DIR / f"job-{job.id}.zip"
        archive_path.unlink(missing_ok=True)
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

            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as output:
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

            job.output_path = str(archive_path)
            job.file_size = archive_path.stat().st_size
            job.status = "completed"
            job.expires_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
                hours=settings.BOOK_ARCHIVE_EXPIRE_HOURS
            )
            await db.commit()
        except Exception as exc:
            archive_path = locals().get("archive_path")
            if isinstance(archive_path, Path):
                archive_path.unlink(missing_ok=True)
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            await db.commit()


def cleanup_expired_book_archives() -> None:
    """清理过期 ZIP 和孤立归档文件。"""
    if not settings.BOOK_ARCHIVE_DIR.exists():
        return
    now = datetime.now(timezone.utc).timestamp()
    for path in settings.BOOK_ARCHIVE_DIR.glob("job-*.zip"):
        if now - path.stat().st_mtime > settings.BOOK_ARCHIVE_EXPIRE_HOURS * 3600:
            path.unlink(missing_ok=True)
