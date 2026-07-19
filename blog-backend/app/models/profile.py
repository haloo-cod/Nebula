"""
Profile + SocialLink 模型 — 个人资料
"""

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Profile(Base, TimestampMixin):
    """单行 singleton 个人资料（id 固定为 1）"""
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    bio_md: Mapped[str] = mapped_column(Text, default="")  # Markdown 原文
    bio_html: Mapped[str] = mapped_column(Text, default="")  # 预渲染 HTML
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    cover_url: Mapped[str] = mapped_column(String(500), default="")


class SocialLink(Base):
    __tablename__ = "social_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50))
    icon: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
