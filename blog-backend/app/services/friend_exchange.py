"""读取交换友链配置，供公开展示和 RSS 频道信息复用。"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_config import SiteConfig
from app.schemas.friend import FriendExchangeInfo


EXCHANGE_CONFIG_KEY = "friends_exchange_info"


async def load_exchange_info(db: AsyncSession) -> FriendExchangeInfo | None:
    """读取有效配置；旧 JSON 缺少 RSS 字段时由 schema 补默认值。"""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == EXCHANGE_CONFIG_KEY))
    config = result.scalar_one_or_none()
    if not config or not config.value:
        return None
    try:
        return FriendExchangeInfo.model_validate(json.loads(config.value))
    except (ValueError, TypeError):
        return None
