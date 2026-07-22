"""主页内容统计接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.gallery import GalleryProject
from app.models.post import Post
from app.schemas.content_stats import ContentStatsResponse
from app.services.moment import get_moment_activity_dates

router = APIRouter(prefix="/content-stats", tags=["主页统计"])


@router.get("", response_model=ContentStatsResponse)
async def get_content_stats(db: AsyncSession = Depends(get_db)):
    """获取主页内容数量和活跃天数。"""
    posts_result = await db.execute(
        select(Post.date).where(Post.is_draft == False)  # noqa: E712
    )
    post_dates = {date[:10] for (date,) in posts_result.all() if date}

    post_count = await db.scalar(
        select(func.count(Post.id)).where(Post.is_draft == False)  # noqa: E712
    )
    gallery_count = await db.scalar(select(func.count(GalleryProject.id)))
    moment_dates, moment_count = get_moment_activity_dates()

    return ContentStatsResponse(
        posts=int(post_count or 0),
        moments=moment_count,
        gallery_projects=int(gallery_count or 0),
        active_days=len(post_dates | moment_dates),
    )
