"""启动迁移不应覆盖图书归档的手动到期时间。"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models.book_download import BookDownloadJob
from app.services.schema_migration import migrate_existing_schema


@pytest.mark.asyncio
async def test_schema_migration_preserves_manual_archive_expiry(tmp_path):
    """重复执行启动迁移时，管理员设置的 expires_at 必须保持不变。"""
    # 使用文件 SQLite，确保迁移调用与建表调用共享同一个数据库连接目标。
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'migration-test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    manual_expiry = datetime(2099, 12, 31, 23, 59, tzinfo=timezone.utc)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            BookDownloadJob(
                id=1,
                user_id=1,
                slugs_json="[]",
                status="completed",
                total_books=1,
                completed_books=1,
                created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
                expires_at=manual_expiry,
            )
        )
        await session.commit()

    await migrate_existing_schema(engine)
    await migrate_existing_schema(engine)

    async with session_factory() as session:
        job = await session.scalar(select(BookDownloadJob).where(BookDownloadJob.id == 1))

    await engine.dispose()

    assert job is not None
    assert job.expires_at is not None
    assert job.expires_at.replace(tzinfo=timezone.utc) == manual_expiry
