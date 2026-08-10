"""Background media-source validation tests."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.services.background import create_background


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_video_background_accepts_null_image_id(db_session):
    result = await create_background(
        db_session,
        image_id=None,
        theme="dark",
        device="desktop",
        media_type="video",
        media_url="/api/v1/files/1/media",
        mime_type="video/mp4",
        file_size=1,
    )
    assert result["media_type"] == "video"
    assert result["url"] == "/api/v1/files/1/media"


@pytest.mark.asyncio
async def test_image_background_still_requires_a_source(db_session):
    with pytest.raises(ValueError, match="image background requires"):
        await create_background(
            db_session,
            image_id=None,
            theme="light",
            device="desktop",
            media_type="image",
        )
