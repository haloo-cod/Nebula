"""
轮播图路由 — 公开列表 + 管理员 CRUD
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.carousel import (
    CarouselListResponse,
    CarouselReorderRequest,
    CarouselSlideCreate,
    CarouselSlideResponse,
)
from app.services.carousel import (
    create_slide,
    delete_slide,
    list_slides,
    reorder_slides,
)

router = APIRouter(prefix="/carousel", tags=["首页轮播"])


@router.get("", response_model=CarouselListResponse)
async def get_carousel(db: AsyncSession = Depends(get_db)):
    """获取首页轮播图列表（公开接口）"""
    items = await list_slides(db)
    return CarouselListResponse(items=items, total=len(items))


@router.post("", response_model=CarouselSlideResponse, status_code=status.HTTP_201_CREATED)
async def add_slide(
    data: CarouselSlideCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """添加轮播图（管理员）"""
    try:
        result = await create_slide(db, image_id=data.image_id, sort_order=data.sort_order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.delete("/{slide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_slide(
    slide_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除轮播图（管理员）"""
    success = await delete_slide(db, slide_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="轮播图不存在")


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder(
    data: CarouselReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量调整轮播图排序（管理员）"""
    await reorder_slides(db, data.ids)
