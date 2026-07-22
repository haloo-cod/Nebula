"""
Friend 模型 — 友链
"""

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Friend(Base, TimestampMixin):
    __tablename__ = "friends"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # 站点名称
    bio: Mapped[str] = mapped_column(Text, default="")  # 简介
    avatar: Mapped[str] = mapped_column(String(500), default="")  # 头像 URL
    url: Mapped[str] = mapped_column(String(500))  # 站点地址
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
