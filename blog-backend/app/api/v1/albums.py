"""
相册路由 — 公开列表/详情 + 管理员 CRUD + 照片管理
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.album import (
    AlbumCreate,
    AlbumDetailResponse,
    AlbumListResponse,
    AlbumPhotoReorderRequest,
    AlbumResponse,
    AlbumUpdate,
    PhotoCreate,
    PhotoUpdate,
    PhotoResponse,
)
from app.services.album import (
    add_photo,
    create_album,
    delete_album,
    get_album_detail,
    list_albums,
    remove_photo,
    reorder_photos,
    update_album,
    update_photo,
)

router = APIRouter(prefix="/albums", tags=["相册"])


# ============ 公开接口 ============


@router.get("", response_model=AlbumListResponse)
async def get_albums(db: AsyncSession = Depends(get_db)):
    """获取相册列表（公开接口）"""
    items = await list_albums(db)
    return AlbumListResponse(items=items, total=len(items))


@router.get("/{album_id}", response_model=AlbumDetailResponse)
async def get_album(album_id: int, db: AsyncSession = Depends(get_db)):
    """获取相册详情（含全部照片，公开接口）"""
    detail = await get_album_detail(db, album_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="相册不存在")
    return detail


# ============ 管理员接口 ============


@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: AlbumCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建相册（管理员）"""
    album = await create_album(db, title=data.title, description=data.description, orientation=data.orientation)
    return AlbumResponse(
        id=album.id,
        title=album.title,
        description=album.description,
        orientation=album.orientation,
        cover_url="",
        cover_image_id=album.cover_image_id,
        photo_count=0,
        date=album.created_at.strftime("%Y.%m") if album.created_at else "",
        created_at=album.created_at,
        preview_photos=[],
    )


@router.put("/{album_id}", response_model=AlbumDetailResponse)
async def update(
    album_id: int,
    data: AlbumUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新相册信息（管理员）"""
    try:
        result = await update_album(
            db,
            album_id,
            title=data.title,
            description=data.description,
            orientation=data.orientation,
            cover_image_id=data.cover_image_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="相册不存在")
    return result


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    album_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除相册（管理员，级联删除照片记录）"""
    success = await delete_album(db, album_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="相册不存在")


# ============ 照片管理 ============


@router.post("/{album_id}/photos", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def add_album_photo(
    album_id: int,
    data: PhotoCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """添加照片到相册（管理员）"""
    try:
        result = await add_photo(db, album_id=album_id, image_id=data.image_id, caption=data.caption)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.delete("/{album_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_album_photo(
    album_id: int,
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """从相册删除照片（管理员）"""
    success = await remove_photo(db, album_id, photo_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="照片不存在")


@router.put("/{album_id}/photos/{photo_id}", response_model=PhotoResponse)
async def update_album_photo(
    album_id: int,
    photo_id: int,
    data: PhotoUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新相册照片说明（管理员）。"""
    result = await update_photo(db, album_id, photo_id, data.caption)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="照片不存在")
    return result


@router.put("/{album_id}/photos/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_album_photos(
    album_id: int,
    data: AlbumPhotoReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量调整照片排序（管理员）"""
    await reorder_photos(db, album_id, data.ids)
