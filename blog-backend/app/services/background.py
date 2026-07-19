"""
背景图 service — CRUD + 排序
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background import Background
from app.models.image import UploadedImage


async def list_backgrounds(
    db: AsyncSession,
    theme: str | None = None,
    device: str | None = None,
) -> list[dict]:
    """
    获取背景图列表，可按 theme/device 过滤
    返回带 url 的字典列表（join uploaded_images 取 url）
    """
    stmt = select(Background, UploadedImage.url).join(
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
            "url": url,
            "theme": bg.theme,
            "device": bg.device,
            "sort_order": bg.sort_order,
            "created_at": bg.created_at,
        }
        for bg, url in rows
    ]


async def create_background(
    db: AsyncSession,
    image_id: int,
    theme: str,
    device: str,
    sort_order: int = 0,
) -> dict:
    """
    创建背景图记录
    验证 image_id 存在后插入 backgrounds 表
    """
    # 验证图片存在
    img_result = await db.execute(
        select(UploadedImage).where(UploadedImage.id == image_id)
    )
    image = img_result.scalar_one_or_none()
    if not image:
        raise ValueError(f"图片 ID {image_id} 不存在")

    bg = Background(
        image_id=image_id,
        theme=theme,
        device=device,
        sort_order=sort_order,
    )
    db.add(bg)
    await db.commit()
    await db.refresh(bg)

    return {
        "id": bg.id,
        "url": image.url,
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

    await db.delete(bg)
    await db.commit()
    return True


async def reorder_backgrounds(db: AsyncSession, ids: list[int]) -> None:
    """
    批量更新排序：ids 列表的顺序即为新的 sort_order（0, 1, 2, ...）
    """
    for order, bg_id in enumerate(ids):
        result = await db.execute(
            select(Background).where(Background.id == bg_id)
        )
        bg = result.scalar_one_or_none()
        if bg:
            bg.sort_order = order

    await db.commit()
