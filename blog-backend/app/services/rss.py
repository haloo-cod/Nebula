"""RSS 2.0 摘要订阅：只读取数据库，不扫描 Markdown 或上传目录。"""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
import re
from urllib.parse import quote
from xml.etree import ElementTree as ET

from sqlalchemy import select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.post import Post
from app.services.friend_exchange import load_exchange_info


BEIJING = timezone(timedelta(hours=8))
FEED_LIMIT = 20
ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
ET.register_namespace("atom", ATOM_NAMESPACE)


class SummaryParser(HTMLParser):
    """提取可见正文，排除脚本、样式和隐藏模板内容。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template", "noscript"}:
            self.hidden += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "pre", "blockquote"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template", "noscript"}:
            self.hidden = max(0, self.hidden - 1)
        elif tag in {"p", "div", "li", "pre", "blockquote"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _utc(value: datetime) -> datetime:
    """SQLite 返回的无时区创建时间按 UTC 解释。"""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _publication_time(post: RowMapping) -> datetime:
    """历史年月日按北京时间解释，非法或空日期回退到创建时间。"""
    value = (post["date"] or "").strip()
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", value):
        try:
            return datetime(*map(int, value.split("-")), tzinfo=BEIJING)
        except ValueError:
            pass
    return _utc(post["created_at"])


def _xml_text(value: str) -> str:
    """过滤 XML 1.0 不支持的控制字符，其余转义交给序列化器。"""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]", "", value)


def _element(parent: ET.Element, name: str, text: str) -> ET.Element:
    child = ET.SubElement(parent, name)
    child.text = _xml_text(text)
    return child


def _summary(content: str) -> str:
    parser = SummaryParser()
    parser.feed(content)
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()[:200]


async def build_rss(db: AsyncSession) -> bytes:
    """生成最近 20 篇公开博文的 RSS；正文仅为缺少简介的入选文章读取。"""
    result = await db.execute(
        select(Post.id, Post.slug, Post.title, Post.description, Post.date,
               Post.category, Post.created_at, Post.updated_at).where(Post.is_draft.is_(False))
    )
    # 先比较真实时间，兼容不补零和无效历史日期；此处不受置顶状态影响。
    posts = sorted(result.mappings().all(), key=lambda post: (
        _publication_time(post), _utc(post["created_at"]), post["id"]
    ), reverse=True)[:FEED_LIMIT]
    missing_descriptions = [post["id"] for post in posts if not (post["description"] or "").strip()]
    bodies = {}
    if missing_descriptions:
        result = await db.execute(select(Post.id, Post.content_html).where(Post.id.in_(missing_descriptions)))
        bodies = dict(result.all())
    info = await load_exchange_info(db)
    site_url = settings.FRONTEND_URL.rstrip("/")
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    _element(channel, "title", (info.name.strip() if info else "") or "Starlitn'blog")
    _element(channel, "link", site_url + "/")
    _element(channel, "description", (info.bio.strip() if info else "") or "分享技术、生活和思考的个人博客")
    _element(channel, "language", "zh-cn")
    _element(channel, "ttl", "5")
    ET.SubElement(channel, f"{{{ATOM_NAMESPACE}}}link", {
        "href": site_url + "/api/v1/rss.xml", "rel": "self", "type": "application/rss+xml"
    })
    if posts:
        _element(channel, "lastBuildDate", format_datetime(max(_utc(post["updated_at"]) for post in posts)))
    for post in posts:
        item = ET.SubElement(channel, "item")
        _element(item, "title", post["title"])
        _element(item, "link", site_url + "/post/" + quote(post["slug"], safe=""))
        guid = _element(item, "guid", f"{site_url}/rss/posts/{post['id']}/{_utc(post['created_at']).isoformat()}")
        guid.set("isPermaLink", "false")
        _element(item, "pubDate", format_datetime(_publication_time(post)))
        _element(item, "description", (post["description"] or "").strip() or _summary(bodies.get(post["id"], "")))
        if post["category"]:
            _element(item, "category", post["category"])
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
