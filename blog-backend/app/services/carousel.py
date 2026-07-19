"""
轮播图 service — CRUD + 排序
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carousel import CarouselSlide
from app.models.image import UploadedImage


async def list_slides(db: AsyncSession) -> list[dict]:
    """获取轮播图列表（按 sort_order 升序）"""
    stmt = (
        select(CarouselSlide, UploadedImage.url)
        .join(UploadedImage, CarouselSlide.image_id == UploadedImage.id)
        .order_by(CarouselSlide.sort_order.asc(), CarouselSlide.id.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": slide.id,
            "url": url,
            "sort_order": slide.sort_order,
            "created_at": slide.created_at,
        }
        for slide, url in rows
    ]


async def create_slide(db: AsyncSession, image_id: int, sort_order: int = 0) -> dict:
    """创建轮播图记录"""
    # 验证图片存在
    img_result = await db.execute(
        select(UploadedImage).where(UploadedImage.id == image_id)
    )
    image = img_result.scalar_one_or_none()
    if not image:
        raise ValueError(f"图片 ID {image_id} 不存在")

    slide = CarouselSlide(image_id=image_id, sort_order=sort_order)
    db.add(slide)
    await db.commit()
    await db.refresh(slide)

    return {
        "id": slide.id,
        "url": image.url,
        "sort_order": slide.sort_order,
        "created_at": slide.created_at,
    }


async def delete_slide(db: AsyncSession, slide_id: int) -> bool:
    """删除轮播图记录"""
    result = await db.execute(
        select(CarouselSlide).where(CarouselSlide.id == slide_id)
    )
    slide = result.scalar_one_or_none()
    if not slide:
        return False

    await db.delete(slide)
    await db.commit()
    return True


async def reorder_slides(db: AsyncSession, ids: list[int]) -> None:
    """批量更新排序"""
    for order, slide_id in enumerate(ids):
        result = await db.execute(
            select(CarouselSlide).where(CarouselSlide.id == slide_id)
        )
        slide = result.scalar_one_or_none()
        if slide:
            slide.sort_order = order

    await db.commit()
