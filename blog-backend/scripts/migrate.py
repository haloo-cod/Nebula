"""独立执行数据库结构迁移：在 blog-backend 目录运行 python -m scripts.migrate。"""

import asyncio
import sys


async def migrate() -> None:
    """只运行配置校验和结构迁移，并始终释放数据库连接。"""
    from app.database import engine

    try:
        # DEBUG 不能让迁移日志输出 SQL 参数中的认证主体或其他私有数据。
        engine.echo = False
        from app.config import validate_production_settings
        from app.services.schema_migration import migrate_existing_schema

        validate_production_settings()
        await migrate_existing_schema(engine)
    finally:
        await engine.dispose()


def main() -> int:
    """以退出码报告结果，避免异常携带配置值、SQL 参数或令牌。"""
    try:
        asyncio.run(migrate())
    except Exception as error:
        print(
            f"Schema migration failed ({type(error).__name__}). "
            "Check production configuration and database access before starting the service.",
            file=sys.stderr,
        )
        return 1
    print("Schema migration completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
