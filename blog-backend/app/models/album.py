"""
Album / AlbumPhoto 模型 — 图片页相册管理
"""

from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Album(Base, TimestampMixin):
    """相册"""
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    orientation: Mapped[str] = mapped_column(String(20), default="portrait")  # 'portrait' | 'landscape'
    cover_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploaded_images.id"), nullable=True, default=None
    )

    # 关联照片列表
    photos: Mapped[list["AlbumPhoto"]] = relationship(
        back_populates="album", cascade="all, delete-orphan", order_by="AlbumPhoto.sort_order"
    )


class AlbumPhoto(Base, TimestampMixin):
    """相册中的单张照片"""
    __tablename__ = "album_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id", ondelete="CASCADE"))
    image_id: Mapped[int] = mapped_column(ForeignKey("uploaded_images.id"))
    caption: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    album: Mapped["Album"] = relationship(back_populates="photos")
