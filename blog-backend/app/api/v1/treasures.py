"""
藏宝阁路由 — 公开列表 + 管理员 CRUD
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.treasure import (
    TreasureCreate,
    TreasureListResponse,
    TreasureResponse,
    TreasureUpdate,
)
from app.services.treasure import (
    create_treasure,
    delete_treasure,
    get_categories,
    list_treasures,
    update_treasure,
)

router = APIRouter(prefix="/treasures", tags=["藏宝阁"])


@router.get("", response_model=TreasureListResponse)
async def get_treasures(
    category: str | None = Query(None, description="分类筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取藏宝列表（公开接口，可按分类筛选）"""
    items = await list_treasures(db, category=category)
    return TreasureListResponse(items=items, total=len(items))


@router.get("/categories", response_model=list[str])
async def get_treasure_categories(db: AsyncSession = Depends(get_db)):
    """获取所有分类列表（公开接口）"""
    return await get_categories(db)


@router.post("", response_model=TreasureResponse, status_code=status.HTTP_201_CREATED)
async def add_treasure(
    data: TreasureCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建藏宝条目（管理员）"""
    treasure = await create_treasure(
        db,
        slug=data.slug,
        title=data.title,
        description=data.description,
        category=data.category,
        icon=data.icon,
        url=data.url,
        download_file=data.download_file,
        tags=data.tags,
        sort_order=data.sort_order,
    )
    return treasure


@router.put("/{treasure_id}", response_model=TreasureResponse)
async def edit_treasure(
    treasure_id: int,
    data: TreasureUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新藏宝条目（管理员）"""
    treasure = await update_treasure(
        db,
        treasure_id,
        title=data.title,
        description=data.description,
        category=data.category,
        icon=data.icon,
        url=data.url,
        download_file=data.download_file,
        tags=data.tags,
        sort_order=data.sort_order,
    )
    if not treasure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="藏宝条目不存在")
    return treasure


@router.delete("/{treasure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_treasure(
    treasure_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除藏宝条目（管理员）"""
    success = await delete_treasure(db, treasure_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="藏宝条目不存在")
