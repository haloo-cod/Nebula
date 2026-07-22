"""
TavernPost 模型 — 深夜酒馆匿名留言
"""

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TavernPost(Base, TimestampMixin):
    __tablename__ = "tavern_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[str] = mapped_column(String(100))  # 匿名署名
    topic: Mapped[str] = mapped_column(String(200))  # 标题/话题标签
    body: Mapped[str] = mapped_column(Text)  # 正文（不限字数）
    ip_hash: Mapped[str] = mapped_column(String(64), default="")  # IP 的 SHA256
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否可见
