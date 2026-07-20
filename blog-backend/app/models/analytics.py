"""访问统计事件模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AnalyticsEvent(Base, TimestampMixin):
    """记录页面访问和下载等行为，原始 IP 仅供管理员统计查看。"""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    path: Mapped[str] = mapped_column(String(500), index=True)
    title: Mapped[str] = mapped_column(String(300), default="")
    referrer: Mapped[str] = mapped_column(String(1000), default="")
    user_agent: Mapped[str] = mapped_column(String(1000), default="")
    ip_address: Mapped[str] = mapped_column(String(80), default="")
    ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    visitor_id: Mapped[str] = mapped_column(String(100), default="", index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
