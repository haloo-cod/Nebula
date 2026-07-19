"""
CarouselSlide 模型 — 首页图片轮播
"""

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CarouselSlide(Base, TimestampMixin):
    __tablename__ = "carousel_slides"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("uploaded_images.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
