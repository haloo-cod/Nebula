"""SQLite 限流服务测试。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.api.v1.auth import _safe_redirect
from app.services.rate_limit import enforce_event_limit


@pytest.mark.asyncio
async def test_rate_limit_is_shared_by_database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await enforce_event_limit(session, "test-ip", "test", 60, 1)
        with pytest.raises(Exception) as error:
            await enforce_event_limit(session, "test-ip", "test", 60, 1)
        assert getattr(error.value, "status_code", None) == 429
    await engine.dispose()


def test_oauth_redirect_only_allows_local_paths():
    assert _safe_redirect('/treasure') == '/treasure'
    assert _safe_redirect('//evil.example') == '/'
    assert _safe_redirect('https://evil.example') == '/'
