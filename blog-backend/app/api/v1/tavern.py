"""
深夜酒馆路由 — 匿名发布 + 管理员管理
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.site_config import SiteConfig
from app.models.user import User
from app.schemas.tavern import (
    TavernAdminListResponse,
    TavernListResponse,
    TavernPostCreate,
    TavernPostResponse,
    VisibilityUpdate,
)
from app.services.tavern import (
    check_rate_limit,
    create_post,
    delete_post,
    hash_ip,
    list_all_posts,
    list_visible_posts,
    set_visibility,
)

router = APIRouter(prefix="/tavern", tags=["深夜酒馆"])


CONFIG_KEY_BG = "tavern_bg_url"


class TavernBgResponse(BaseModel):
    bg_url: str = ""


@router.get("/config", response_model=TavernBgResponse)
async def get_tavern_config(db: AsyncSession = Depends(get_db)):
    """获取酒馆背景图配置（公开接口）"""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == CONFIG_KEY_BG))
    config = result.scalar_one_or_none()
    return TavernBgResponse(bg_url=config.value if config else "")


class TavernBgUpdate(BaseModel):
    bg_url: str = ""


@router.put("/config", response_model=TavernBgResponse)
async def update_tavern_config(
    data: TavernBgUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """设置酒馆背景图（管理员）"""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == CONFIG_KEY_BG))
    config = result.scalar_one_or_none()
    if config:
        config.value = data.bg_url
    else:
        db.add(SiteConfig(key=CONFIG_KEY_BG, value=data.bg_url, description="酒馆背景图 URL"))
    await db.commit()
    return TavernBgResponse(bg_url=data.bg_url)


@router.get("", response_model=TavernListResponse)
async def get_tavern_posts(db: AsyncSession = Depends(get_db)):
    """获取可见留言列表（公开接口）"""
    items = await list_visible_posts(db)
    return TavernListResponse(items=items, total=len(items))


@router.post("", response_model=TavernPostResponse, status_code=status.HTTP_201_CREATED)
async def submit_tavern_post(
    data: TavernPostCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """发布留言（匿名，IP 限频：每小时最多 3 条）"""
    # 获取客户端 IP
    client_ip = request.client.host if request.client else "unknown"
    ip_hash_value = hash_ip(client_ip)

    # 检查限频
    allowed = await check_rate_limit(db, ip_hash_value)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="发言太频繁了，休息一下再来吧（每小时最多 3 条）",
        )

    # 创建留言
    post = await create_post(db, author=data.author, topic=data.topic, body=data.body, client_ip=client_ip)
    return post


@router.get("/all", response_model=TavernAdminListResponse)
async def get_all_posts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取全部留言（管理员，含隐藏的）"""
    items = await list_all_posts(db)
    return TavernAdminListResponse(items=items, total=len(items))


@router.put("/{post_id}/visibility", response_model=TavernPostResponse)
async def update_visibility(
    post_id: int,
    data: VisibilityUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """设置留言可见/隐藏（管理员）"""
    post = await set_visibility(db, post_id, data.is_visible)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除留言（管理员）"""
    success = await delete_post(db, post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
