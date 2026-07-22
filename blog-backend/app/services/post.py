"""
博文 service — .md 文件读写 + DB 元数据管理
"""

from pathlib import Path
import re

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


def safe_post_slug(value: str) -> str:
    """规范化导入文章 slug，拒绝路径穿越和空值。"""
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "-", value.strip()).strip("-_")
    return slug[:180] or "imported-post"


def build_post_markdown(post, content_md: str) -> str:
    """将文章元数据和正文导出为可再次导入的 Markdown。"""
    tags = ", ".join(post.tags or [])
    metadata = [
        "---",
        f"title: {post.title}",
        f"slug: {post.slug}",
        f"date: {post.date}",
        f"description: {post.description}",
        f"category: {post.category}",
        f"tags: [{tags}]",
        f"draft: {'true' if post.is_draft else 'false'}",
        f"pinned: {'true' if post.is_pinned else 'false'}",
        "---",
        "",
    ]
    return "\n".join(metadata) + content_md.lstrip()


def parse_post_markdown(content: str, filename: str) -> dict:
    """解析简单 YAML Front Matter，兼容无 Front Matter 的普通 Markdown。"""
    metadata: dict[str, object] = {}
    body = content
    if content.startswith("---"):
        parts = content.split("\n---", 1)
        if len(parts) == 2:
            header = parts[0][3:].strip("\n")
            body = parts[1].lstrip("\n")
            for line in header.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                value = value.strip().strip('"\'')
                if key.strip() == "tags":
                    value = value.strip("[]")
                    metadata[key.strip()] = [item.strip().strip('"\'') for item in value.split(",") if item.strip()]
                elif key.strip() in {"draft", "pinned"}:
                    metadata[key.strip()] = value.lower() in {"true", "1", "yes"}
                else:
                    metadata[key.strip()] = value

    stem = Path(filename).stem
    title = str(metadata.get("title") or "")
    if not title:
        heading = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), "")
        title = heading or stem
    return {
        "slug": safe_post_slug(str(metadata.get("slug") or stem)),
        "title": title[:300],
        "date": str(metadata.get("date") or ""),
        "description": str(metadata.get("description") or ""),
        "category": str(metadata.get("category") or ""),
        "tags": metadata.get("tags") if isinstance(metadata.get("tags"), list) else [],
        "is_draft": bool(metadata.get("draft", True)),
        "is_pinned": bool(metadata.get("pinned", False)),
        "content_md": body,
    }
