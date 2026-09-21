"""
Book 模型 — EPUB 电子书索引
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    author: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(String(500), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    # 相对于 uploads/books/ 的文件路径
    file_path: Mapped[str] = mapped_column(String(500), default="")
    storage_backend: Mapped[str] = mapped_column(String(20), default="local")  # 'local' | 'r2'
    r2_key: Mapped[str | None] = mapped_column(String(500), nullable=True)  # R2 对象键（EPUB 文件）
