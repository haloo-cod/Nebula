"""账户化评论模型。"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    """页面评论及回复；legacy_author 用于保留历史匿名评论。"""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_key: Mapped[str] = mapped_column(String(300), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), index=True, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    legacy_author: Mapped[str] = mapped_column(String(100), default="")
    legacy_avatar_color: Mapped[str] = mapped_column(String(20), default="")

    user = relationship("User")
