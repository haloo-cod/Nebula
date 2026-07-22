"""
友链路由 — 公开列表 + 管理员 CRUD
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.friend import (
    FriendCreate,
    FriendListResponse,
    FriendResponse,
    FriendUpdate,
    FriendExchangeInfo,
)
from app.models.site_config import SiteConfig
from app.services.friend import (
    create_friend,
    delete_friend,
    list_friends,
    update_friend,
)

router = APIRouter(prefix="/friends", tags=["友链"])

EXCHANGE_CONFIG_KEY = "friends_exchange_info"


def default_exchange_info() -> FriendExchangeInfo:
    """返回交换友链的默认展示内容。"""
    return FriendExchangeInfo(
        name="你的站点名称",
        url="https://example.com",
        avatar="https://api.dicebear.com/9.x/adventurer/svg?seed=myblog",
        bio="这里填写你的站点简介。",
        requirements=["原创内容优先", "站点稳定可访问", "无违法违规内容", "最好有定期更新"],
        contact="your-email@example.com",
    )


@router.get("/exchange-info", response_model=FriendExchangeInfo)
async def get_exchange_info(db: AsyncSession = Depends(get_db)):
    """获取交换友链展示信息。"""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == EXCHANGE_CONFIG_KEY))
    config = result.scalar_one_or_none()
    if not config or not config.value:
        return default_exchange_info()
    try:
        return FriendExchangeInfo.model_validate(json.loads(config.value))
    except (ValueError, TypeError):
        return default_exchange_info()


@router.put("/exchange-info", response_model=FriendExchangeInfo)
async def update_exchange_info(
    data: FriendExchangeInfo,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新交换友链展示信息。"""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == EXCHANGE_CONFIG_KEY))
    config = result.scalar_one_or_none()
    value = json.dumps(data.model_dump(), ensure_ascii=False)
    if config:
        config.value = value
    else:
        db.add(SiteConfig(key=EXCHANGE_CONFIG_KEY, value=value, description="交换友链展示信息"))
    await db.commit()
    return data


@router.get("", response_model=FriendListResponse)
async def get_friends(db: AsyncSession = Depends(get_db)):
    """获取友链列表（公开接口）"""
    items = await list_friends(db)
    return FriendListResponse(items=items, total=len(items))


@router.post("", response_model=FriendResponse, status_code=status.HTTP_201_CREATED)
async def add_friend(
    data: FriendCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """添加友链（管理员）"""
    friend = await create_friend(
        db, name=data.name, bio=data.bio, avatar=data.avatar, url=data.url, sort_order=data.sort_order
    )
    return friend


@router.put("/{friend_id}", response_model=FriendResponse)
async def edit_friend(
    friend_id: int,
    data: FriendUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新友链（管理员）"""
    friend = await update_friend(
        db, friend_id, name=data.name, bio=data.bio, avatar=data.avatar, url=data.url, sort_order=data.sort_order
    )
    if not friend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="友链不存在")
    return friend


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    friend_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除友链（管理员）"""
    success = await delete_friend(db, friend_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="友链不存在")
