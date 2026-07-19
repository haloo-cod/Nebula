"""
友链 service — CRUD
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friend import Friend


async def list_friends(db: AsyncSession) -> list[Friend]:
    """获取友链列表（按 sort_order 升序）"""
    result = await db.execute(
        select(Friend).order_by(Friend.sort_order.asc(), Friend.id.asc())
    )
    return list(result.scalars().all())


async def create_friend(
    db: AsyncSession,
    name: str,
    url: str,
    bio: str = "",
    avatar: str = "",
    sort_order: int = 0,
) -> Friend:
    """创建友链"""
    friend = Friend(name=name, bio=bio, avatar=avatar, url=url, sort_order=sort_order)
    db.add(friend)
    await db.commit()
    await db.refresh(friend)
    return friend


async def update_friend(
    db: AsyncSession,
    friend_id: int,
    name: str | None = None,
    bio: str | None = None,
    avatar: str | None = None,
    url: str | None = None,
    sort_order: int | None = None,
) -> Friend | None:
    """更新友链"""
    result = await db.execute(select(Friend).where(Friend.id == friend_id))
    friend = result.scalar_one_or_none()
    if not friend:
        return None

    if name is not None:
        friend.name = name
    if bio is not None:
        friend.bio = bio
    if avatar is not None:
        friend.avatar = avatar
    if url is not None:
        friend.url = url
    if sort_order is not None:
        friend.sort_order = sort_order

    await db.commit()
    await db.refresh(friend)
    return friend


async def delete_friend(db: AsyncSession, friend_id: int) -> bool:
    """删除友链"""
    result = await db.execute(select(Friend).where(Friend.id == friend_id))
    friend = result.scalar_one_or_none()
    if not friend:
        return False

    await db.delete(friend)
    await db.commit()
    return True
