"""公开 RSS 订阅接口。"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.rss import build_rss


router = APIRouter(tags=["RSS 订阅"])


@router.get("/rss.xml", response_class=Response, responses={200: {"content": {"application/rss+xml": {}}}})
async def get_rss(db: AsyncSession = Depends(get_db)) -> Response:
    """匿名访问也始终只返回已发布博文，缓存有效期为五分钟。"""
    return Response(await build_rss(db), media_type="application/rss+xml; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=300"})
