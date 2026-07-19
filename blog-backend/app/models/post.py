"""
Post 模型 — 博文元数据 + 预渲染 HTML
"""

from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    date: Mapped[str] = mapped_column(String(20), default="")  # YYYY-MM-DD
    cover_url: Mapped[str] = mapped_column(String(500), default="")
    category: Mapped[str] = mapped_column(String(50), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    content_html: Mapped[str] = mapped_column(Text, default="")
    # md_filename 对应 content/posts/ 下的文件名
    md_filename: Mapped[str] = mapped_column(String(300), default="")
