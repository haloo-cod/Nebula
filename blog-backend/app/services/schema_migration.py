"""轻量启动迁移，用于无完整 Alembic 历史的现有 SQLite 数据库。"""

from contextlib import AsyncExitStack
from pathlib import Path
from uuid import uuid4

from filelock import AsyncFileLock
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models import Base
from app.models.friend import Friend
from app.models.friend_application import FriendApplication
from app.models.schema_migration import SchemaMigration
from app.models.user import User

AUTH_IDENTITY_MIGRATION = "20261023_auth_identity_uuid"


async def migrate_existing_schema(engine: AsyncEngine) -> None:
    """串行补齐旧表，并以持久版本记录保证认证身份仅切换一次。"""

    async with AsyncExitStack() as stack:
        database = engine.url.database
        if engine.dialect.name == "sqlite" and database and database != ":memory:":
            await stack.enter_async_context(AsyncFileLock(f"{Path(database).resolve()}.migration.lock", timeout=60))
        conn = await stack.enter_async_context(engine.begin())
        if conn.dialect.name == "sqlite":
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))
            # 先取得写锁再检查字段，避免多个 worker 同时读到旧结构并重复执行 ALTER。
            # 显式事务也确保 SQLite 的建表、改表与数据迁移一起提交或回滚。
            await conn.execute(text("BEGIN IMMEDIATE"))
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "sqlite":
            application_sql = await conn.scalar(text(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'friend_applications'"
            ))
            if application_sql and "AUTOINCREMENT" not in application_sql.upper():
                # 只升级申请表；保留全部 ID/审核/关联数据，旧讨论地址不能指向新申请。
                metadata = MetaData()
                User.__table__.to_metadata(metadata)
                Friend.__table__.to_metadata(metadata)
                replacement = FriendApplication.__table__.to_metadata(metadata, name="friend_applications_upgraded")
                await conn.execute(CreateTable(replacement))
                columns = ", ".join(f'"{column.name}"' for column in FriendApplication.__table__.columns)
                await conn.execute(text(
                    f"INSERT INTO friend_applications_upgraded ({columns}) SELECT {columns} FROM friend_applications"
                ))
                await conn.execute(text("DROP TABLE friend_applications"))
                await conn.execute(text("ALTER TABLE friend_applications_upgraded RENAME TO friend_applications"))
                for index in FriendApplication.__table__.indexes:
                    await conn.execute(CreateIndex(index))
        friend_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("friends")}
        )
        if "rss_url" not in friend_columns:
            await conn.execute(text("ALTER TABLE friends ADD COLUMN rss_url VARCHAR(2048) NOT NULL DEFAULT ''"))
        bg_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("backgrounds")}
        )
        bg_image_nullable = await conn.run_sync(
            lambda sync_conn: next(
                (column["nullable"] for column in inspect(sync_conn).get_columns("backgrounds") if column["name"] == "image_id"),
                True,
            )
        )
        if not bg_image_nullable and conn.dialect.name == "sqlite":
            await conn.execute(text("ALTER TABLE backgrounds RENAME TO backgrounds_legacy"))
            await conn.execute(text("""
                CREATE TABLE backgrounds (
                    id INTEGER NOT NULL PRIMARY KEY,
                    image_id INTEGER,
                    media_type VARCHAR(10) NOT NULL DEFAULT 'image',
                    media_url VARCHAR(1000) NOT NULL DEFAULT '',
                    poster_url VARCHAR(1000) NOT NULL DEFAULT '',
                    mime_type VARCHAR(100) NOT NULL DEFAULT '',
                    file_size INTEGER NOT NULL DEFAULT 0,
                    theme VARCHAR(10) NOT NULL,
                    device VARCHAR(10) NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY(image_id) REFERENCES uploaded_images (id),
                    CONSTRAINT ck_background_single_media_source CHECK (
                        (media_type = 'video' AND image_id IS NULL AND media_url <> '') OR
                        (media_type = 'image' AND ((image_id IS NOT NULL AND media_url = '') OR
                        (image_id IS NULL AND media_url <> '')))
                    )
                )
            """))
            await conn.execute(text("""
                INSERT INTO backgrounds (id, image_id, theme, device, sort_order, created_at, updated_at)
                SELECT id, image_id, theme, device, sort_order, created_at, updated_at FROM backgrounds_legacy
            """))
            await conn.execute(text("DROP TABLE backgrounds_legacy"))
            bg_columns = {"id", "image_id", "media_type", "media_url", "poster_url", "mime_type", "file_size", "theme", "device", "sort_order", "created_at", "updated_at"}
        for field, definition in {
            "media_type": "VARCHAR(10) NOT NULL DEFAULT 'image'",
            "media_url": "VARCHAR(1000) NOT NULL DEFAULT ''",
            "poster_url": "VARCHAR(1000) NOT NULL DEFAULT ''",
            "mime_type": "VARCHAR(100) NOT NULL DEFAULT ''",
            "file_size": "INTEGER NOT NULL DEFAULT 0",
            "source_text": "VARCHAR(120) NOT NULL DEFAULT ''",
            "source_url": "VARCHAR(2048) NOT NULL DEFAULT ''",
        }.items():
            if field not in bg_columns:
                await conn.execute(text(f"ALTER TABLE backgrounds ADD COLUMN {field} {definition}"))
        await conn.execute(text("UPDATE backgrounds SET media_type = 'image' WHERE media_type IS NULL OR media_type = ''"))
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
            "auth_id": "VARCHAR(36) NOT NULL DEFAULT ''",
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

        session_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("auth_sessions")}
        )
        if "auth_id" not in session_columns:
            await conn.execute(text("ALTER TABLE auth_sessions ADD COLUMN auth_id VARCHAR(36) NOT NULL DEFAULT ''"))
        await conn.run_sync(SchemaMigration.__table__.create, checkfirst=True)
        applied = await conn.scalar(
            text("SELECT version FROM schema_migrations WHERE version = :version"),
            {"version": AUTH_IDENTITY_MIGRATION},
        )
        if applied is None:
            missing_ids = (await conn.execute(
                text("SELECT id FROM users WHERE auth_id IS NULL OR auth_id = ''")
            )).scalars().all()
            if missing_ids:
                await conn.execute(
                    text("UPDATE users SET auth_id = :auth_id WHERE id = :id"),
                    [{"id": user_id, "auth_id": str(uuid4())} for user_id in missing_ids],
                )
            # 旧会话无法证明签发时的账户身份，统一撤销，不能关联到迁移时的同号用户。
            await conn.execute(text("UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE revoked_at IS NULL"))
            await conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": AUTH_IDENTITY_MIGRATION},
            )
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_auth_id ON users (auth_id)"))

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
        # 不要在启动迁移中重算 expires_at。
        # 该字段既保存创建归档时的默认到期时间，也保存管理员手动延期后的时间；
        # 每次启动都按 created_at 重写会覆盖手动设置，并可能立即触发过期清理。
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_events_occurred_at ON analytics_events (occurred_at)"))

        # R2 对象存储字段：storage_backend 记录文件实际位置，r2_key 为对象键。
        r2_columns = {
            "uploaded_images": "ix_uploaded_images_storage_backend",
            "uploaded_files": "ix_uploaded_files_storage_backend",
            "backgrounds": "ix_backgrounds_storage_backend",
            "books": "ix_books_storage_backend",
        }
        for table, index_name in r2_columns.items():
            table_columns = await conn.run_sync(
                lambda sync_conn, t=table: {
                    column["name"] for column in inspect(sync_conn).get_columns(t)
                }
            )
            if "storage_backend" not in table_columns:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN storage_backend VARCHAR(20) NOT NULL DEFAULT 'local'")
                )
            if "r2_key" not in table_columns:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN r2_key VARCHAR(500)"))
            await conn.execute(
                text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} (storage_backend)")
            )
