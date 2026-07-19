"""
GalleryProject 模型
"""

from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GalleryProject(Base, TimestampMixin):
    __tablename__ = "gallery_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="")
    year: Mapped[str] = mapped_column(String(10), default="")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    content_html: Mapped[str] = mapped_column(Text, default="")
    md_filename: Mapped[str] = mapped_column(String(300), default="")
