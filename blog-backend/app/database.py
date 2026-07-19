"""
SQLAlchemy async engine + session 管理
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI 依赖：获取数据库 session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
