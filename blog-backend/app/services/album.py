"""
相册 service — CRUD + 照片管理
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.album import Album, AlbumPhoto
from app.models.image import UploadedImage


def _format_date(dt) -> str:
    """格式化日期为 'YYYY.MM'"""
    return dt.strftime("%Y.%m") if dt else ""


async def _get_cover_url(db: AsyncSession, album: Album, photos_data: list | None = None) -> str:
    """
    获取相册封面 URL
    优先级: cover_image_id 指定的图 > 第一张照片 > 空字符串
    """
    if album.cover_image_id:
        result = await db.execute(
            select(UploadedImage.url).where(UploadedImage.id == album.cover_image_id)
        )
        url = result.scalar_one_or_none()
        if url:
            return url

    # 取第一张照片的 URL
    if photos_data:
        return photos_data[0]["url"] if photos_data else ""

    result = await db.execute(
        select(UploadedImage.url)
        .join(AlbumPhoto, AlbumPhoto.image_id == UploadedImage.id)
        .where(AlbumPhoto.album_id == album.id)
        .order_by(AlbumPhoto.sort_order.asc())
        .limit(1)
    )
    url = result.scalar_one_or_none()
    return url or ""


async def list_albums(db: AsyncSession) -> list[dict]:
    """获取相册列表（含封面 URL、照片数量和前 3 张预览图）"""
    # 查询所有相册
    stmt = select(Album).order_by(Album.created_at.desc())
    result = await db.execute(stmt)
    albums = list(result.scalars().all())

    items = []
    for album in albums:
        # 照片数量
        count_result = await db.execute(
            select(func.count(AlbumPhoto.id)).where(AlbumPhoto.album_id == album.id)
        )
        photo_count = count_result.scalar() or 0

        # 前 3 张预览照片（用于卡片堆叠效果）
        preview_stmt = (
            select(AlbumPhoto, UploadedImage.url)
            .join(UploadedImage, AlbumPhoto.image_id == UploadedImage.id)
            .where(AlbumPhoto.album_id == album.id)
            .order_by(AlbumPhoto.sort_order.asc())
            .limit(3)
        )
        preview_result = await db.execute(preview_stmt)
        preview_photos = [
            {
                "id": p.id,
                "url": url,
                "caption": p.caption,
                "sort_order": p.sort_order,
                "created_at": p.created_at,
            }
            for p, url in preview_result.all()
        ]

        cover_url = await _get_cover_url(db, album, preview_photos)

        items.append({
            "id": album.id,
            "title": album.title,
            "description": album.description,
            "orientation": album.orientation,
            "cover_url": cover_url,
            "photo_count": photo_count,
            "date": _format_date(album.created_at),
            "created_at": album.created_at,
            "preview_photos": preview_photos,
        })

    return items


async def get_album_detail(db: AsyncSession, album_id: int) -> dict | None:
    """获取相册详情（含完整照片列表）"""
    result = await db.execute(
        select(Album).options(selectinload(Album.photos)).where(Album.id == album_id)
    )
    album = result.scalar_one_or_none()
    if not album:
        return None

    # 获取每张照片的 URL
    photos_data = []
    for photo in sorted(album.photos, key=lambda p: p.sort_order):
        img_result = await db.execute(
            select(UploadedImage.url).where(UploadedImage.id == photo.image_id)
        )
        url = img_result.scalar_one_or_none() or ""
        photos_data.append({
            "id": photo.id,
            "url": url,
            "caption": photo.caption,
            "sort_order": photo.sort_order,
            "created_at": photo.created_at,
        })

    cover_url = await _get_cover_url(db, album, photos_data)

    return {
        "id": album.id,
        "title": album.title,
        "description": album.description,
        "orientation": album.orientation,
        "cover_url": cover_url,
        "photo_count": len(photos_data),
        "date": _format_date(album.created_at),
        "created_at": album.created_at,
        "photos": photos_data,
    }


async def create_album(
    db: AsyncSession,
    title: str,
    description: str = "",
    orientation: str = "portrait",
) -> Album:
    """创建相册"""
    album = Album(title=title, description=description, orientation=orientation)
    db.add(album)
    await db.commit()
    await db.refresh(album)
    return album


async def update_album(
    db: AsyncSession,
    album_id: int,
    title: str | None = None,
    description: str | None = None,
    orientation: str | None = None,
    cover_image_id: int | None = None,
) -> dict | None:
    """更新相册信息"""
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        return None

    if title is not None:
        album.title = title
    if description is not None:
        album.description = description
    if orientation is not None:
        album.orientation = orientation
    if cover_image_id is not None:
        # 验证图片存在
        img_result = await db.execute(
            select(UploadedImage).where(UploadedImage.id == cover_image_id)
        )
        if not img_result.scalar_one_or_none():
            raise ValueError(f"图片 ID {cover_image_id} 不存在")
        album.cover_image_id = cover_image_id

    await db.commit()
    return await get_album_detail(db, album_id)


async def delete_album(db: AsyncSession, album_id: int) -> bool:
    """删除相册（级联删除照片记录，不删图片文件）"""
    result = await db.execute(select(Album).where(Album.id == album_id))
    album = result.scalar_one_or_none()
    if not album:
        return False

    await db.delete(album)
    await db.commit()
    return True


async def add_photo(
    db: AsyncSession,
    album_id: int,
    image_id: int,
    caption: str | None = None,
) -> dict:
    """添加照片到相册"""
    # 验证相册存在
    album_result = await db.execute(select(Album).where(Album.id == album_id))
    if not album_result.scalar_one_or_none():
        raise ValueError(f"相册 ID {album_id} 不存在")

    # 验证图片存在
    img_result = await db.execute(
        select(UploadedImage).where(UploadedImage.id == image_id)
    )
    image = img_result.scalar_one_or_none()
    if not image:
        raise ValueError(f"图片 ID {image_id} 不存在")

    # 获取当前最大 sort_order
    max_order_result = await db.execute(
        select(func.max(AlbumPhoto.sort_order)).where(AlbumPhoto.album_id == album_id)
    )
    max_order = max_order_result.scalar() or 0

    photo = AlbumPhoto(
        album_id=album_id,
        image_id=image_id,
        caption=caption,
        sort_order=max_order + 1,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return {
        "id": photo.id,
        "url": image.url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
        "created_at": photo.created_at,
    }


async def remove_photo(db: AsyncSession, album_id: int, photo_id: int) -> bool:
    """从相册删除照片"""
    result = await db.execute(
        select(AlbumPhoto).where(
            AlbumPhoto.id == photo_id,
            AlbumPhoto.album_id == album_id,
        )
    )
    photo = result.scalar_one_or_none()
    if not photo:
        return False

    await db.delete(photo)
    await db.commit()
    return True


async def reorder_photos(db: AsyncSession, album_id: int, ids: list[int]) -> None:
    """批量调整照片排序"""
    for order, photo_id in enumerate(ids):
        result = await db.execute(
            select(AlbumPhoto).where(
                AlbumPhoto.id == photo_id,
                AlbumPhoto.album_id == album_id,
            )
        )
        photo = result.scalar_one_or_none()
        if photo:
            photo.sort_order = order

    await db.commit()
