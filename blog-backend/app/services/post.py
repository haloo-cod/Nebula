"""
博文 service — .md 文件读写 + DB 元数据管理
"""

from pathlib import Path

from app.config import settings
from app.services.markdown import render_markdown

POSTS_DIR = settings.CONTENT_DIR / "posts"


def read_md_file(md_filename: str) -> str:
    """从 content/posts/ 读取 Markdown 原文"""
    path = POSTS_DIR / md_filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_md_file(md_filename: str, content: str) -> None:
    """写入 Markdown 文件到 content/posts/"""
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / md_filename
    path.write_text(content, encoding="utf-8")


def delete_md_file(md_filename: str) -> None:
    """删除 .md 文件"""
    path = POSTS_DIR / md_filename
    if path.exists():
        path.unlink()


def render_post_content(md_content: str) -> str:
    """渲染 Markdown 为 HTML"""
    return render_markdown(md_content)


def slug_to_filename(slug: str) -> str:
    """slug → 文件名"""
    return f"{slug}.md"
