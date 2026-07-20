"""
关于页路由 — 读取和更新 about.md 内容
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.config import settings
from app.database import get_db
from app.models.site_config import SiteConfig
from app.models.user import User
from app.schemas.about import AboutContent

router = APIRouter(prefix="/about", tags=["关于"])


@router.get("/content", response_model=AboutContent)
async def get_about_content(db: AsyncSession = Depends(get_db)):
    """获取关于页 Markdown 内容"""
    about_file = settings.CONTENT_DIR / "about.md"
    content = about_file.read_text(encoding="utf-8") if about_file.exists() else ""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == "about_cover_url"))
    cover_config = result.scalar_one_or_none()
    return {"content_md": content, "cover_url": cover_config.value if cover_config else ""}


@router.put("/content", response_model=AboutContent)
async def update_about_content(
    data: AboutContent,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """由管理员更新关于页 Markdown 内容。"""

    settings.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    about_file = settings.CONTENT_DIR / "about.md"
    temp_file = settings.CONTENT_DIR / f".about.{uuid.uuid4().hex}.tmp"
    try:
        temp_file.write_text(data.content_md, encoding="utf-8")
        temp_file.replace(about_file)
    finally:
        temp_file.unlink(missing_ok=True)
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == "about_cover_url"))
    cover_config = result.scalar_one_or_none()
    if cover_config:
        cover_config.value = data.cover_url
    else:
        db.add(
            SiteConfig(
                key="about_cover_url",
                value=data.cover_url,
                description="关于页独立封面图 URL",
            )
        )
    await db.commit()
    return data
