"""
Markdown 渲染工具（markdown-it-py）
"""

from markdown_it import MarkdownIt

# 不允许 Markdown 原文注入 HTML，避免后台内容通过 v-html 形成 XSS。
_md = MarkdownIt("commonmark", {"html": False}).enable("table")


def render_markdown(content: str) -> str:
    """将 Markdown 原文渲染为 HTML"""
    return _md.render(content)
