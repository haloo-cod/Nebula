"""启动迁移需保留已有数据，且支持多个 worker 并发启动。"""

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models.book_download import BookDownloadJob
from app.models.background import Background
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


@pytest.mark.asyncio
async def test_background_source_migration_preserves_media_and_storage(tmp_path):
    """旧版背景连续迁移两次，媒体、排序和对象存储字段保持原值。"""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'background-source.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(Background(id=7, media_type="video", media_url="/api/v1/files/5/media",
                               poster_url="https://example.com/poster.jpg", mime_type="video/mp4", file_size=500,
                               theme="dark", device="desktop", sort_order=3, storage_backend="r2", r2_key="backgrounds/test.mp4"))
        await session.commit()
    async with engine.begin() as connection:
        await connection.execute(text("ALTER TABLE backgrounds DROP COLUMN source_text"))
        await connection.execute(text("ALTER TABLE backgrounds DROP COLUMN source_url"))
        before = (await connection.execute(text("SELECT * FROM backgrounds ORDER BY id"))).mappings().all()
    await migrate_existing_schema(engine)
    await migrate_existing_schema(engine)
    async with engine.connect() as connection:
        after = (await connection.execute(text("SELECT * FROM backgrounds ORDER BY id"))).mappings().all()
        assert [{key: row[key] for key in before[0]} for row in after] == before
        assert after[0]["source_text"] == after[0]["source_url"] == ""
    await engine.dispose()


@pytest.mark.asyncio
async def test_background_source_migration_serializes_workers(tmp_path):
    """两个独立连接池同时迁移旧表，不重复加列且保留全部原有背景字段。"""
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'concurrent-background-source.db'}"
    engines = [create_async_engine(database_url, connect_args={"timeout": 5}) for _ in range(2)]
    try:
        async with engines[0].begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engines[0], expire_on_commit=False)() as session:
            session.add(Background(id=7, media_type="video", media_url="/api/v1/files/5/media",
                                   theme="dark", device="desktop", sort_order=3,
                                   storage_backend="r2", r2_key="backgrounds/test.mp4"))
            await session.commit()
        async with engines[0].begin() as connection:
            await connection.execute(text("ALTER TABLE backgrounds DROP COLUMN source_text"))
            await connection.execute(text("ALTER TABLE backgrounds DROP COLUMN source_url"))
            before = (await connection.execute(text("SELECT * FROM backgrounds ORDER BY id"))).mappings().all()

        @event.listens_for(engines[0].sync_engine, "before_cursor_execute")
        def pause_before_adding_source(conn, cursor, statement, parameters, context, executemany):
            """在检查与改表之间给另一个 worker 时间，稳定覆盖此前的并发竞态。"""
            if statement.startswith("ALTER TABLE backgrounds ADD COLUMN source_text"):
                conn.connection.dbapi_connection.run_async(lambda _: asyncio.sleep(0.15))

        results = await asyncio.gather(
            *(migrate_existing_schema(engine) for engine in engines), return_exceptions=True,
        )
        assert results == [None, None]
        async with engines[0].connect() as connection:
            after = (await connection.execute(text("SELECT * FROM backgrounds ORDER BY id"))).mappings().all()
            assert [{key: row[key] for key in before[0]} for row in after] == before
            assert after[0]["source_text"] == after[0]["source_url"] == ""
    finally:
        for engine in engines:
            await engine.dispose()
