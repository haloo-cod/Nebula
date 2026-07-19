"""
关于页路由 — 返回 about.md 内容
"""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/about", tags=["关于"])


@router.get("/content")
async def get_about_content():
    """获取关于页 Markdown 内容"""
    about_file = settings.CONTENT_DIR / "about.md"
    if not about_file.exists():
        return {"content_md": ""}
    content = about_file.read_text(encoding="utf-8")
    return {"content_md": content}
