"""
UploadedFile 模型 — 藏宝阁等功能使用的通用下载文件记录
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UploadedFile(Base, TimestampMixin):
    """通用上传文件，实际文件存放于 uploads/files。"""

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), unique=True)
    original_name: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(500), default="")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[str] = mapped_column(String(200), default="")
