"""轻量启动迁移，用于无完整 Alembic 历史的现有 SQLite 数据库。"""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine


async def migrate_existing_schema(engine: AsyncEngine) -> None:
    """幂等补齐现有 SQLite 数据库中后续版本增加的字段。"""

    async with engine.begin() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("books")}
        )
        if "sort_order" not in columns:
            await conn.execute(text("ALTER TABLE books ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"))
            rows = (
                await conn.execute(text("SELECT id FROM books ORDER BY created_at ASC, id ASC"))
            ).scalars().all()
            for index, book_id in enumerate(rows):
                await conn.execute(
                    text("UPDATE books SET sort_order = :sort_order WHERE id = :book_id"),
                    {"sort_order": index, "book_id": book_id},
                )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_books_sort_order ON books (sort_order)")
        )

        user_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("users")}
        )
        user_fields = {
            "email": "VARCHAR(320)",
            "display_name": "VARCHAR(100) NOT NULL DEFAULT ''",
            "avatar_url": "VARCHAR(500) NOT NULL DEFAULT ''",
            "github_id": "VARCHAR(100)",
            "email_verified": "BOOLEAN NOT NULL DEFAULT 0",
            "is_active": "BOOLEAN NOT NULL DEFAULT 1",
            "last_login_at": "DATETIME",
        }
        for field, definition in user_fields.items():
            if field not in user_columns:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {field} {definition}"))
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_github_id ON users (github_id)"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_book_download_jobs_status ON book_download_jobs (status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_book_download_jobs_expires_at ON book_download_jobs (expires_at)"))
        download_job_columns = await conn.run_sync(
            lambda sync_conn: {
                column["name"]
                for column in inspect(sync_conn).get_columns("book_download_jobs")
            }
        )
        if "archive_name" not in download_job_columns:
            await conn.execute(
                text("ALTER TABLE book_download_jobs ADD COLUMN archive_name VARCHAR(160) NOT NULL DEFAULT 'starlit-books'")
            )
        if "expire_days" not in download_job_columns:
            await conn.execute(
                text("ALTER TABLE book_download_jobs ADD COLUMN expire_days INTEGER NOT NULL DEFAULT 7")
            )
        # 7 天策略上线前创建的已完成任务仍可能保留旧的 1 小时过期时间。
        await conn.execute(
            text(
                "UPDATE book_download_jobs "
                "SET expires_at = datetime(created_at, '+168 hours') "
                "WHERE status = 'completed' AND expires_at IS NOT NULL"
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_events_occurred_at ON analytics_events (occurred_at)"))
