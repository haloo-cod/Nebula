"""
展览页 service — .md 文件读写
"""

from app.config import settings
from app.services.markdown import render_markdown

GALLERY_DIR = settings.CONTENT_DIR / "gallery"


def read_md_file(md_filename: str) -> str:
    """从 content/gallery/ 读取 Markdown 原文"""
    path = GALLERY_DIR / md_filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_md_file(md_filename: str, content: str) -> None:
    """写入 Markdown 文件到 content/gallery/"""
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    path = GALLERY_DIR / md_filename
    path.write_text(content, encoding="utf-8")


def delete_md_file(md_filename: str) -> None:
    """删除 .md 文件"""
    path = GALLERY_DIR / md_filename
    if path.exists():
        path.unlink()


def render_gallery_content(md_content: str) -> str:
    """渲染 Markdown 为 HTML"""
    return render_markdown(md_content)


def slug_to_filename(slug: str) -> str:
    """slug → 文件名"""
    return f"{slug}.md"
