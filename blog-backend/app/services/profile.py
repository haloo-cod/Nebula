"""
个人资料 service — Profile + SocialLinks
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile, SocialLink


async def get_profile(db: AsyncSession) -> dict:
    """获取个人资料（singleton，id=1）"""
    result = await db.execute(select(Profile).where(Profile.id == 1))
    profile = result.scalar_one_or_none()

    # 社交链接
    links_result = await db.execute(
        select(SocialLink).order_by(SocialLink.sort_order.asc(), SocialLink.id.asc())
    )
    links = list(links_result.scalars().all())

    if not profile:
        return {
            "name": "",
            "bio": "",
            "avatar_url": "",
            "cover_url": "",
            "social_links": [],
        }

    return {
        "name": profile.name,
        "bio": profile.bio_md,
        "avatar_url": profile.avatar_url,
        "cover_url": profile.cover_url,
        "social_links": links,
    }


async def update_profile(
    db: AsyncSession,
    name: str | None = None,
    bio: str | None = None,
    avatar_url: str | None = None,
    cover_url: str | None = None,
) -> dict:
    """更新个人资料"""
    result = await db.execute(select(Profile).where(Profile.id == 1))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = Profile(id=1, name=name or "", bio_md=bio or "", avatar_url=avatar_url or "", cover_url=cover_url or "")
        db.add(profile)
    else:
        if name is not None:
            profile.name = name
        if bio is not None:
            profile.bio_md = bio
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if cover_url is not None:
            profile.cover_url = cover_url

    await db.commit()
    return await get_profile(db)


async def add_social_link(
    db: AsyncSession,
    label: str,
    icon: str,
    url: str,
    sort_order: int = 0,
) -> SocialLink:
    """添加社交链接"""
    link = SocialLink(label=label, icon=icon, url=url, sort_order=sort_order)
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def delete_social_link(db: AsyncSession, link_id: int) -> bool:
    """删除社交链接"""
    result = await db.execute(select(SocialLink).where(SocialLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        return False
    await db.delete(link)
    await db.commit()
    return True
