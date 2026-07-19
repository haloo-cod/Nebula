"""
友链路由 — 公开列表 + 管理员 CRUD
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.friend import (
    FriendCreate,
    FriendListResponse,
    FriendResponse,
    FriendUpdate,
)
from app.services.friend import (
    create_friend,
    delete_friend,
    list_friends,
    update_friend,
)

router = APIRouter(prefix="/friends", tags=["友链"])


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
