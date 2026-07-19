"""
个人资料路由 — 公开获取 + 管理员更新
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdate,
    SocialLinkCreate,
    SocialLinkResponse,
)
from app.services.profile import (
    add_social_link,
    delete_social_link,
    get_profile,
    update_profile,
)

router = APIRouter(prefix="/profile", tags=["个人资料"])


@router.get("", response_model=ProfileResponse)
async def get_site_profile(db: AsyncSession = Depends(get_db)):
    """获取个人资料（公开接口）"""
    return await get_profile(db)


@router.put("", response_model=ProfileResponse)
async def update_site_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新个人资料（管理员）"""
    return await update_profile(
        db, name=data.name, bio=data.bio, avatar_url=data.avatar_url, cover_url=data.cover_url
    )


@router.post("/social-links", response_model=SocialLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_social_link(
    data: SocialLinkCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """添加社交链接（管理员）"""
    return await add_social_link(db, label=data.label, icon=data.icon, url=data.url, sort_order=data.sort_order)


@router.delete("/social-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_social_link(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除社交链接（管理员）"""
    success = await delete_social_link(db, link_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="社交链接不存在")
