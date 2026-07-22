"""基于 SQLite 的跨 worker 限流辅助。"""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rate_limit import RateLimitHit
from app.services.analytics import utc_now


async def enforce_event_limit(
    db: AsyncSession,
    key_hash: str,
    event_type: str,
    window_seconds: int,
    maximum: int,
) -> None:
    """按哈希键和事件类型限制近期请求，超限返回 429。"""
    now = utc_now()
    since = now - timedelta(seconds=window_seconds)
    result = await db.execute(
        select(func.count(RateLimitHit.id)).where(
            RateLimitHit.event_type == event_type,
            RateLimitHit.key_hash == key_hash,
            RateLimitHit.occurred_at >= since,
        )
    )
    if int(result.scalar() or 0) >= maximum:
        retry_after = max(1, window_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": str(retry_after)},
        )
    db.add(RateLimitHit(event_type=event_type, key_hash=key_hash, occurred_at=now))
    await db.commit()
