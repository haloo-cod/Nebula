"""图书归档路径、状态和排序测试。"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.books import _job_response
from app.models import Base
from app.models.book_download import BookDownloadJob
from app.services import book_download


@pytest.fixture
def archive_directory(tmp_path, monkeypatch):
    """为归档路径测试提供独立临时目录。"""
    monkeypatch.setattr(book_download.settings, "BOOK_ARCHIVE_DIR", tmp_path)
    return tmp_path


def make_job(job_id: int, *, output_path: str, status: str = "completed") -> BookDownloadJob:
    """创建不依赖数据库提交的归档任务对象。"""
    return BookDownloadJob(
        id=job_id,
        user_id=1,
        slugs_json="[]",
        status=status,
        total_books=1,
        completed_books=1,
        output_path=output_path,
        archive_name="test-archive",
        expire_days=7,
        file_size=10,
        error_message="",
        created_at=datetime.now(timezone.utc),
    )


def test_archive_path_ignores_legacy_absolute_path(archive_directory):
    """历史数据库路径不应影响当前环境的归档文件定位。"""
    legacy_path = "/home/starlit/My_blog/blog-backend/uploads/book-archives/job-5.zip"
    job = make_job(5, output_path=legacy_path)

    current_path = archive_directory / "job-5.zip"
    current_path.write_bytes(b"zip")

    assert book_download.archive_path(job.id) == current_path
    assert book_download.existing_archive_path(job) == current_path


def test_missing_archive_is_reported(archive_directory):
    """数据库记录存在但当前文件不存在时应返回 missing。"""
    job = make_job(5, output_path="/old/environment/job-5.zip")

    response = _job_response(job)

    assert response.status == "missing"
    assert response.download_url is None


def test_expired_archive_is_not_downloadable(archive_directory):
    """过期归档不能继续提供下载地址。"""
    path = archive_directory / "job-5.zip"
    path.write_bytes(b"zip")
    job = make_job(5, output_path="/old/environment/job-5.zip")
    job.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    response = _job_response(job)

    assert response.status == "expired"
    assert response.download_url is None


@pytest.mark.asyncio
async def test_archive_order_is_stable_after_deletion():
    """删除中间任务后，剩余任务保持创建时间和 ID 的稳定顺序。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    created_at = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    async with session_factory() as session:
        for job_id in (1, 2, 3, 4, 5):
            session.add(
                BookDownloadJob(
                    id=job_id,
                    user_id=1,
                    slugs_json="[]",
                    status="completed",
                    total_books=1,
                    completed_books=1,
                    created_at=created_at,
                    output_path=f"job-{job_id}.zip",
                )
            )
        await session.commit()

        await session.delete(await session.get(BookDownloadJob, 4))
        await session.commit()

        result = await session.execute(
            select(BookDownloadJob)
            .where(BookDownloadJob.user_id == 1)
            .order_by(BookDownloadJob.created_at.desc(), BookDownloadJob.id.desc())
        )
        remaining_ids = [job.id for job in result.scalars().all()]

    await engine.dispose()

    assert remaining_ids == [5, 3, 2, 1]
    assert 4 not in remaining_ids
