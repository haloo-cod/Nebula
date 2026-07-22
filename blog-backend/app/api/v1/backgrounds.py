"""
背景图路由 — 公开列表 + 管理员 CRUD
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.background import (
    BackgroundCreate,
    BackgroundListResponse,
    BackgroundReorderRequest,
    BackgroundResponse,
)
from app.services.background import (
    create_background,
    delete_background,
    list_backgrounds,
    reorder_backgrounds,
)

router = APIRouter(prefix="/backgrounds", tags=["背景图"])


@router.get("", response_model=BackgroundListResponse)
async def get_backgrounds(
    theme: str | None = Query(None, description="主题过滤: dark / light"),
    device: str | None = Query(None, description="设备过滤: desktop / mobile"),
    db: AsyncSession = Depends(get_db),
):
    """获取背景图列表（公开接口，可按 theme/device 筛选）"""
    items = await list_backgrounds(db, theme=theme, device=device)
    return BackgroundListResponse(items=items, total=len(items))


@router.post("", response_model=BackgroundResponse, status_code=status.HTTP_201_CREATED)
async def add_background(
    data: BackgroundCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建背景图记录（管理员）"""
    try:
        result = await create_background(
            db,
            image_id=data.image_id,
            theme=data.theme,
            device=data.device,
            sort_order=data.sort_order,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.delete("/{bg_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_background(
    bg_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除背景图记录（管理员，不删除图片文件）"""
    success = await delete_background(db, bg_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="背景图不存在")


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder(
    data: BackgroundReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量调整背景图排序（管理员）"""
    await reorder_backgrounds(db, data.ids)
