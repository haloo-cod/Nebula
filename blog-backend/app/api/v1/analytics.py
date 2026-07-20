"""访问统计接口。"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.config import settings
from app.database import get_db
from app.models.analytics import AnalyticsEvent
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsOverview,
    AnalyticsPublicSummary,
    AnalyticsPageItem,
    AnalyticsTrendItem,
    AnalyticsVisitorItem,
    AnalyticsVisitorResponse,
)
from app.services.analytics import get_client_ip, hash_ip, utc_now
from app.services.rate_limit import enforce_event_limit

router = APIRouter(prefix="/analytics", tags=["访问统计"])
TRACKABLE_EVENTS = {"page_view", "book_open", "book_download", "file_download", "zip_download"}


def day_start(days_ago: int = 0) -> datetime:
    now = utc_now()
    return (now - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def record_event(
    data: AnalyticsEventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """接收公开访问事件，IP 和 User-Agent 从请求中提取。"""
    if not settings.ANALYTICS_ENABLED or data.event_type not in TRACKABLE_EVENTS:
        return
    ip_address = get_client_ip(request)
    ip_hash = hash_ip(ip_address)
    await enforce_event_limit(db, ip_hash, "analytics_ingest", 60, 30)
    event = AnalyticsEvent(
        event_type=data.event_type,
        path=data.path,
        title=data.title,
        referrer=data.referrer,
        user_agent=request.headers.get("user-agent", "")[:1000],
        ip_address=ip_address,
        ip_hash=ip_hash,
        visitor_id=data.visitor_id,
        user_id=None,
        occurred_at=utc_now(),
    )
    db.add(event)
    await db.commit()


def _range_filter(days: int):
    return AnalyticsEvent.occurred_at >= day_start(days - 1)


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """获取访问概览。"""
    today = day_start()
    yesterday = day_start(1)
    page_view = AnalyticsEvent.event_type == "page_view"

    async def count(condition):
        return int((await db.execute(select(func.count(AnalyticsEvent.id)).where(condition))).scalar() or 0)

    async def unique(condition):
        return int((await db.execute(select(func.count(distinct(AnalyticsEvent.ip_hash))).where(condition))).scalar() or 0)

    return AnalyticsOverview(
        today_pv=await count(page_view & (AnalyticsEvent.occurred_at >= today)),
        today_uv=await unique(page_view & (AnalyticsEvent.occurred_at >= today)),
        yesterday_pv=await count(page_view & (AnalyticsEvent.occurred_at >= yesterday) & (AnalyticsEvent.occurred_at < today)),
        yesterday_uv=await unique(page_view & (AnalyticsEvent.occurred_at >= yesterday) & (AnalyticsEvent.occurred_at < today)),
        total_pv=await count(page_view),
        total_uv=await unique(page_view),
        page_views=await count(page_view),
        book_downloads=await count(AnalyticsEvent.event_type == "book_download"),
        zip_downloads=await count(AnalyticsEvent.event_type == "zip_download"),
    )


@router.get("/public-summary", response_model=AnalyticsPublicSummary)
async def public_summary(db: AsyncSession = Depends(get_db)):
    """获取前台可展示的访问聚合数据。"""
    today = day_start()
    page_view = AnalyticsEvent.event_type == "page_view"

    async def count(condition):
        return int((await db.execute(select(func.count(AnalyticsEvent.id)).where(condition))).scalar() or 0)

    async def unique(condition):
        return int((await db.execute(select(func.count(distinct(AnalyticsEvent.ip_hash))).where(condition))).scalar() or 0)

    trend_items: list[AnalyticsTrendItem] = []
    for offset in range(6, -1, -1):
        start = day_start(offset)
        end = start + timedelta(days=1)
        condition = page_view & (AnalyticsEvent.occurred_at >= start) & (AnalyticsEvent.occurred_at < end)
        trend_items.append(
            AnalyticsTrendItem(
                date=start.date().isoformat(),
                pv=await count(condition),
                uv=await unique(condition),
            )
        )

    return AnalyticsPublicSummary(
        today_pv=await count(page_view & (AnalyticsEvent.occurred_at >= today)),
        today_uv=await unique(page_view & (AnalyticsEvent.occurred_at >= today)),
        total_pv=await count(page_view),
        total_uv=await unique(page_view),
        trend=trend_items,
    )


@router.get("/trend", response_model=list[AnalyticsTrendItem])
async def trend(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """获取最近 7 天 PV/UV 趋势。"""
    result: list[AnalyticsTrendItem] = []
    for offset in range(6, -1, -1):
        start = day_start(offset)
        end = start + timedelta(days=1)
        condition = (AnalyticsEvent.event_type == "page_view") & (AnalyticsEvent.occurred_at >= start) & (AnalyticsEvent.occurred_at < end)
        pv = int((await db.execute(select(func.count(AnalyticsEvent.id)).where(condition))).scalar() or 0)
        uv = int((await db.execute(select(func.count(distinct(AnalyticsEvent.ip_hash))).where(condition))).scalar() or 0)
        result.append(AnalyticsTrendItem(date=start.date().isoformat(), pv=pv, uv=uv))
    return result


@router.get("/pages", response_model=list[AnalyticsPageItem])
async def pages(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """获取热门页面排行。"""
    result = await db.execute(
        select(AnalyticsEvent.path, func.max(AnalyticsEvent.title), func.count(AnalyticsEvent.id), func.count(distinct(AnalyticsEvent.ip_hash)))
        .where(AnalyticsEvent.event_type == "page_view")
        .group_by(AnalyticsEvent.path)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(10)
    )
    return [AnalyticsPageItem(path=path, title=title or path, pv=pv, uv=uv) for path, title, pv, uv in result.all()]


@router.get("/visitors", response_model=AnalyticsVisitorResponse)
async def visitors(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    ip: str = Query("", max_length=80),
    event_type: str = Query("", max_length=40),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """查看最近访问记录和原始 IP。"""
    conditions = []
    if ip.strip():
        conditions.append(AnalyticsEvent.ip_address == ip.strip())
    if event_type.strip():
        conditions.append(AnalyticsEvent.event_type == event_type.strip())
    query = select(AnalyticsEvent)
    count_query = select(func.count(AnalyticsEvent.id))
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = int((await db.execute(count_query)).scalar() or 0)
    result = await db.execute(
        query.order_by(AnalyticsEvent.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [AnalyticsVisitorItem(id=e.id, event_type=e.event_type, path=e.path, title=e.title, ip_address=e.ip_address, user_agent=e.user_agent, referrer=e.referrer, occurred_at=e.occurred_at) for e in result.scalars().all()]
    return AnalyticsVisitorResponse(items=items, total=total)


@router.delete("/events/expired", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expired_events(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """删除超过配置保留期的访问明细。"""
    cutoff = utc_now() - timedelta(days=settings.ANALYTICS_IP_RETENTION_DAYS)
    result = await db.execute(select(AnalyticsEvent).where(AnalyticsEvent.occurred_at < cutoff))
    for event in result.scalars().all():
        await db.delete(event)
    await db.commit()
