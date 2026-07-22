"""
Background 模型 — 背景图（引用图床中的图片）
"""

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Background(Base, TimestampMixin):
    __tablename__ = "backgrounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("uploaded_images.id"))
    theme: Mapped[str] = mapped_column(String(10))  # 'dark' | 'light'
    device: Mapped[str] = mapped_column(String(10))  # 'desktop' | 'mobile'
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
