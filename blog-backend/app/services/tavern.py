"""
深夜酒馆 service — 匿名留言 CRUD + IP 限频
"""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tavern import TavernPost


# 限频配置：每 IP 每小时最多 3 条
RATE_LIMIT_WINDOW_HOURS = 1
RATE_LIMIT_MAX_POSTS = 3


def hash_ip(ip: str) -> str:
    """对 IP 地址做 SHA256 哈希（不存明文，保护隐私）"""
    return hashlib.sha256(ip.encode()).hexdigest()


async def list_visible_posts(db: AsyncSession) -> list[TavernPost]:
    """获取所有可见留言（按创建时间倒序）"""
    result = await db.execute(
        select(TavernPost)
        .where(TavernPost.is_visible == True)  # noqa: E712
        .order_by(TavernPost.created_at.desc())
    )
    return list(result.scalars().all())


async def list_all_posts(db: AsyncSession) -> list[TavernPost]:
    """获取全部留言（管理员，含隐藏的）"""
    result = await db.execute(
        select(TavernPost).order_by(TavernPost.created_at.desc())
    )
    return list(result.scalars().all())


async def check_rate_limit(db: AsyncSession, ip_hash_value: str) -> bool:
    """
    检查 IP 是否超出发帖限频
    返回 True 表示允许发帖，False 表示超限
    """
    window_start = datetime.now(timezone.utc) - timedelta(hours=RATE_LIMIT_WINDOW_HOURS)
    result = await db.execute(
        select(func.count(TavernPost.id)).where(
            TavernPost.ip_hash == ip_hash_value,
            TavernPost.created_at >= window_start,
        )
    )
    count = result.scalar() or 0
    return count < RATE_LIMIT_MAX_POSTS


async def create_post(
    db: AsyncSession,
    author: str,
    topic: str,
    body: str,
    client_ip: str,
) -> TavernPost:
    """创建留言（含 IP 哈希）"""
    post = TavernPost(
        author=author,
        topic=topic,
        body=body,
        ip_hash=hash_ip(client_ip),
        is_visible=True,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def set_visibility(db: AsyncSession, post_id: int, is_visible: bool) -> TavernPost | None:
    """设置留言可见/隐藏"""
    result = await db.execute(select(TavernPost).where(TavernPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return None

    post.is_visible = is_visible
    await db.commit()
    await db.refresh(post)
    return post


async def delete_post(db: AsyncSession, post_id: int) -> bool:
    """彻底删除留言"""
    result = await db.execute(select(TavernPost).where(TavernPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return False

    await db.delete(post)
    await db.commit()
    return True
