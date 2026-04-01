from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, Date, JSON
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String, primary_key=True)          # arxiv id
    title: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[list] = mapped_column(JSON, default=[])
    abstract: Mapped[str] = mapped_column(Text, default="")
    categories: Mapped[list] = mapped_column(JSON, default=[])
    published: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    url: Mapped[str] = mapped_column(String, default="")
    pdf_url: Mapped[str] = mapped_column(String, default="")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g. "20 pages"

    # AI outputs
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # User interaction
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    summary_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Selection
    fetch_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_disliked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class FetchLog(Base):
    __tablename__ = "fetch_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, default="running")  # running|done|error
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    selected_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AppSetting(Base):
    """Key-value store for persisted settings (supplements env vars)."""
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[object] = mapped_column(JSON, nullable=True)
