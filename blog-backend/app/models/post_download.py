"""文章 Markdown 批量导出任务模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PostDownloadJob(Base, TimestampMixin):
    """记录文章 ZIP 生成状态和临时文件。"""

    __tablename__ = "post_download_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    slugs_json: Mapped[str] = mapped_column(Text)
    archive_name: Mapped[str] = mapped_column(String(160), default="starlit-posts")
    include_images: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    total_posts: Mapped[int] = mapped_column(Integer, default=0)
    completed_posts: Mapped[int] = mapped_column(Integer, default=0)
    output_path: Mapped[str] = mapped_column(String(500), default="")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
