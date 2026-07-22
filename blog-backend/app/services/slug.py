"""统一的 URL slug 生成工具。"""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def slugify(value: str, fallback: str = "item") -> str:
    """将标题转换为稳定、安全且可读的 slug，保留中文和字母数字。"""
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "-", normalized, flags=re.UNICODE)
    normalized = re.sub(r"[-_]+", "-", normalized).strip("-")
    return (normalized or fallback)[:180]


async def unique_slug(
    db: AsyncSession,
    model,
    value: str,
    fallback: str = "item",
    exclude_id: int | None = None,
) -> str:
    """生成数据库中未占用的 slug，重复时追加数字后缀。"""
    base = slugify(value, fallback)
    candidate = base
    suffix = 2
    while True:
        query = select(model.id).where(model.slug == candidate)
        if exclude_id is not None:
            query = query.where(model.id != exclude_id)
        if (await db.execute(query)).scalar_one_or_none() is None:
            return candidate
        candidate = f"{base[: max(1, 180 - len(str(suffix)) - 1)]}-{suffix}"
        suffix += 1
