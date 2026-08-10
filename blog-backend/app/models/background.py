"""
Background 模型 — 背景图（引用图床中的图片）
"""

from sqlalchemy import String, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Background(Base, TimestampMixin):
    __tablename__ = "backgrounds"
    __table_args__ = (
        CheckConstraint(
            "(media_type = 'video' AND image_id IS NULL AND media_url <> '') OR "
            "(media_type = 'image' AND ((image_id IS NOT NULL AND media_url = '') OR "
            "(image_id IS NULL AND media_url <> '')))",
            name="ck_background_single_media_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("uploaded_images.id"), nullable=True)
    media_type: Mapped[str] = mapped_column(String(10), default="image", nullable=False)
    media_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    poster_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    theme: Mapped[str] = mapped_column(String(10))  # 'dark' | 'light'
    device: Mapped[str] = mapped_column(String(10))  # 'desktop' | 'mobile'
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
