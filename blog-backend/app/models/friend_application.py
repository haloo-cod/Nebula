"""友链申请及审核记录，私有联络字段独立于正式友链。"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FriendApplication(Base, TimestampMixin):
    __tablename__ = "friend_applications"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_friend_application_status"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(500))
    avatar: Mapped[str] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(320))
    rss_url: Mapped[str] = mapped_column(String(2048), default="", server_default="")
    status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending", index=True)
    friend_id: Mapped[int | None] = mapped_column(ForeignKey("friends.id", ondelete="CASCADE"), unique=True)
    active_site_key: Mapped[str | None] = mapped_column(String(2048), unique=True)
    review_note: Mapped[str] = mapped_column(Text, default="", server_default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
