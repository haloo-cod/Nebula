"""
关于页路由 — 读取和更新 about.md 内容
"""

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.config import settings
from app.models.user import User
from app.schemas.about import AboutContent

router = APIRouter(prefix="/about", tags=["关于"])


@router.get("/content", response_model=AboutContent)
async def get_about_content():
    """获取关于页 Markdown 内容"""
    about_file = settings.CONTENT_DIR / "about.md"
    if not about_file.exists():
        return {"content_md": ""}
    content = about_file.read_text(encoding="utf-8")
    return {"content_md": content}


@router.put("/content", response_model=AboutContent)
async def update_about_content(
    data: AboutContent,
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
    return data
