from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class SyncState(Base):
    """Tracks last successful sync per data source for incremental ingestion."""

    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    last_sync_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    events_synced: Mapped[int] = mapped_column(Integer, default=0)
