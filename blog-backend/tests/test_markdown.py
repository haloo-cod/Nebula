"""Markdown 输出的基础安全测试。"""

from app.services.markdown import render_markdown


def test_raw_html_is_escaped():
    html = render_markdown('<script>alert(1)</script>\n\n[链接](javascript:alert(1))')

    assert '<script>' not in html
    assert '<a ' not in html
