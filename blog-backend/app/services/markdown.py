"""
Markdown 渲染工具（markdown-it-py）
"""

from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": True}).enable("table")


def render_markdown(content: str) -> str:
    """将 Markdown 原文渲染为 HTML"""
    return _md.render(content)
