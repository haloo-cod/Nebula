"""图书批量下载任务模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BookDownloadJob(Base, TimestampMixin):
    """记录后台生成 EPUB ZIP 的状态和临时文件。"""

    __tablename__ = "book_download_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    slugs_json: Mapped[str] = mapped_column(Text)
    archive_name: Mapped[str] = mapped_column(String(160), default="starlit-books")
    expire_days: Mapped[int] = mapped_column(Integer, default=7)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    total_books: Mapped[int] = mapped_column(Integer, default=0)
    completed_books: Mapped[int] = mapped_column(Integer, default=0)
    output_path: Mapped[str] = mapped_column(String(500), default="")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
