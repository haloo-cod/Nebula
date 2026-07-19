"""
藏宝阁 service — CRUD
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.treasure import Treasure


async def list_treasures(db: AsyncSession, category: str | None = None) -> list[Treasure]:
    """获取藏宝列表（可按分类筛选，按 sort_order 升序）"""
    stmt = select(Treasure).order_by(Treasure.sort_order.asc(), Treasure.id.asc())
    if category:
        stmt = stmt.where(Treasure.category == category)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_treasure_by_slug(db: AsyncSession, slug: str) -> Treasure | None:
    """按 slug 获取单条"""
    result = await db.execute(select(Treasure).where(Treasure.slug == slug))
    return result.scalar_one_or_none()


async def create_treasure(
    db: AsyncSession,
    slug: str,
    title: str,
    description: str = "",
    category: str = "工具",
    icon: str = "",
    url: str = "",
    download_file: str = "",
    tags: list[str] | None = None,
    sort_order: int = 0,
) -> Treasure:
    """创建藏宝条目"""
    treasure = Treasure(
        slug=slug,
        title=title,
        description=description,
        category=category,
        icon=icon,
        url=url,
        download_file=download_file,
        tags=tags or [],
        sort_order=sort_order,
    )
    db.add(treasure)
    await db.commit()
    await db.refresh(treasure)
    return treasure


async def update_treasure(
    db: AsyncSession,
    treasure_id: int,
    title: str | None = None,
    description: str | None = None,
    category: str | None = None,
    icon: str | None = None,
    url: str | None = None,
    download_file: str | None = None,
    tags: list[str] | None = None,
    sort_order: int | None = None,
) -> Treasure | None:
    """更新藏宝条目"""
    result = await db.execute(select(Treasure).where(Treasure.id == treasure_id))
    treasure = result.scalar_one_or_none()
    if not treasure:
        return None

    if title is not None:
        treasure.title = title
    if description is not None:
        treasure.description = description
    if category is not None:
        treasure.category = category
    if icon is not None:
        treasure.icon = icon
    if url is not None:
        treasure.url = url
    if download_file is not None:
        treasure.download_file = download_file
    if tags is not None:
        treasure.tags = tags
    if sort_order is not None:
        treasure.sort_order = sort_order

    await db.commit()
    await db.refresh(treasure)
    return treasure


async def delete_treasure(db: AsyncSession, treasure_id: int) -> bool:
    """删除藏宝条目"""
    result = await db.execute(select(Treasure).where(Treasure.id == treasure_id))
    treasure = result.scalar_one_or_none()
    if not treasure:
        return False

    await db.delete(treasure)
    await db.commit()
    return True


async def get_categories(db: AsyncSession) -> list[str]:
    """获取所有分类列表（去重）"""
    result = await db.execute(
        select(Treasure.category).distinct().order_by(Treasure.category)
    )
    return [row[0] for row in result.all()]
