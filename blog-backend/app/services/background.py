"""
背景图 service — CRUD + 排序
"""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background import Background
from app.models.image import UploadedImage
from app.config import settings
from app.services.analytics import utc_now


def _local_background_path(media_url: str) -> Path | None:
    """Return a local uploaded video path only for our generated URL format."""
    prefixes = ("/uploads/backgrounds/", "/api/v1/backgrounds/media/")
    prefix = next((item for item in prefixes if media_url.startswith(item)), None)
    if prefix is None:
        return None
    name = media_url.removeprefix(prefix)
    if not name or Path(name).name != name:
        return None
    path = (settings.UPLOAD_DIR / "backgrounds" / name).resolve()
    root = (settings.UPLOAD_DIR / "backgrounds").resolve()
    return path if path.parent == root else None


async def list_backgrounds(
    db: AsyncSession,
    theme: str | None = None,
    device: str | None = None,
) -> list[dict]:
    """
    获取背景图列表，可按 theme/device 过滤
    返回带 url 的字典列表（join uploaded_images 取 url）
    """
    stmt = select(Background, UploadedImage.url).outerjoin(
        UploadedImage, Background.image_id == UploadedImage.id
    )
    if theme:
        stmt = stmt.where(Background.theme == theme)
    if device:
        stmt = stmt.where(Background.device == device)
    stmt = stmt.order_by(Background.sort_order.asc(), Background.id.asc())

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": bg.id,
            "url": bg.media_url or url or "",
            "media_type": bg.media_type,
            "poster_url": bg.poster_url,
            "mime_type": bg.mime_type,
            "file_size": bg.file_size,
            "theme": bg.theme,
            "device": bg.device,
            "sort_order": bg.sort_order,
            "created_at": bg.created_at,
        }
        for bg, url in rows
    ]


async def create_background(
    db: AsyncSession,
    image_id: int | None,
    theme: str,
    device: str,
    sort_order: int = 0,
    media_type: str = "image",
    media_url: str = "",
    poster_url: str = "",
    mime_type: str = "",
    file_size: int = 0,
) -> dict:
    """
    创建背景图记录
    验证 image_id 存在后插入 backgrounds 表
    """
    # 验证图片存在
    if media_type == "video" and (not media_url or image_id is not None):
        raise ValueError("video background requires media_url")
    if media_type == "image" and bool(image_id) == bool(media_url):
        raise ValueError("image background requires image_id or media_url")
    image = None
    if image_id is not None:
        img_result = await db.execute(
            select(UploadedImage).where(UploadedImage.id == image_id)
        )
        image = img_result.scalar_one_or_none()
        if image is None:
            raise ValueError(f"图片 ID {image_id} 不存在")

    bg = Background(
        image_id=image_id,
        media_type=media_type,
        media_url=media_url,
        poster_url=poster_url,
        mime_type=mime_type,
        file_size=file_size,
        theme=theme,
        device=device,
        sort_order=sort_order,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(bg)
    await db.commit()
    await db.refresh(bg)

    return {
        "id": bg.id,
        "url": media_url or (image.url if image else ""),
        "media_type": media_type,
        "poster_url": poster_url,
        "mime_type": mime_type,
        "file_size": file_size,
        "theme": bg.theme,
        "device": bg.device,
        "sort_order": bg.sort_order,
        "created_at": bg.created_at,
    }


async def delete_background(db: AsyncSession, bg_id: int) -> bool:
    """
    删除背景图记录（不删除关联的图片文件）
    返回是否成功删除
    """
    result = await db.execute(
        select(Background).where(Background.id == bg_id)
    )
    bg = result.scalar_one_or_none()
    if not bg:
        return False

    local_path = _local_background_path(bg.media_url) if bg.media_type == "video" else None
    await db.delete(bg)
    await db.commit()
    if local_path:
        # A single uploaded asset may be referenced by several background rows.
        refs = await db.execute(select(Background.id).where(Background.media_url == str(bg.media_url)))
        if refs.first() is None:
            local_path.unlink(missing_ok=True)
    return True


async def reorder_backgrounds(
    db: AsyncSession,
    ids: list[int],
    theme: str,
    device: str,
) -> None:
    """
    批量更新排序：ids 列表的顺序即为新的 sort_order（0, 1, 2, ...）
    """
    if len(ids) != len(set(ids)):
        raise ValueError("排序列表包含重复背景图")

    result = await db.execute(
        select(Background).where(Background.theme == theme, Background.device == device)
    )
    group = list(result.scalars().all())
    group_by_id = {bg.id: bg for bg in group}
    if set(ids) != set(group_by_id):
        raise ValueError("排序列表必须包含当前主题和设备分组的全部背景图")

    for order, bg_id in enumerate(ids):
        group_by_id[bg_id].sort_order = order

    await db.commit()
