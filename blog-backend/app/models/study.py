"""
自习室模型 — StudyTodo / ScheduleItem / StudyHistory
"""

from sqlalchemy import String, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class StudyTodo(Base, TimestampMixin):
    __tablename__ = "study_todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=25)
    break_minutes: Mapped[int] = mapped_column(Integer, default=5)
    remaining_seconds: Mapped[float] = mapped_column(Float, default=0)
    completed_pomodoros: Mapped[int] = mapped_column(Integer, default=0)
    today_completed: Mapped[int] = mapped_column(Integer, default=0)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ScheduleItem(Base, TimestampMixin):
    __tablename__ = "study_schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    start_time: Mapped[str] = mapped_column(String(10), default="")  # HH:MM
    end_time: Mapped[str] = mapped_column(String(10), default="")  # HH:MM
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)


class StudyHistory(Base, TimestampMixin):
    __tablename__ = "study_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10), unique=True, index=True)  # YYYY-MM-DD
    completed_pomodoros: Mapped[int] = mapped_column(Integer, default=0)
    total_focus_minutes: Mapped[int] = mapped_column(Integer, default=0)
