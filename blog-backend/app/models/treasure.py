"""
Treasure 模型 — 藏宝阁条目
开源项目 / 工具 → url 跳转
资源下载 → download_file 提供文件下载
"""

from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Treasure(Base, TimestampMixin):
    __tablename__ = "treasures"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50))  # '开源项目' | '工具' | '资源下载'
    icon: Mapped[str] = mapped_column(String(100), default="")
    url: Mapped[str] = mapped_column(String(500), default="")  # 外跳链接
    download_file: Mapped[str] = mapped_column(String(500), default="")  # 下载文件路径
    tags: Mapped[list] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(default=0)
