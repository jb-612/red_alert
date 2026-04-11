"""ACLED pre-computed aggregate rows sourced from Explorer static overview files."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class AcledAggregate(Base):
    """One row per (bucket, country, disorder_type) from an ACLED overview file."""

    __tablename__ = "acled_aggregates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bucket_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    granularity: Mapped[str] = mapped_column(String(10), nullable=False)
    country_id: Mapped[int] = mapped_column(Integer, nullable=False)
    country_name: Mapped[str] = mapped_column(Text, nullable=False)
    disorder_type: Mapped[str] = mapped_column(String(40), nullable=False)
    events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fatalities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exposure: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    exposure_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0)
    theater: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    latest_update: Mapped[date] = mapped_column(Date, nullable=False)
    source_file: Mapped[str] = mapped_column(String(80), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    __table_args__ = (
        Index("idx_acled_agg_bucket_gran", "bucket_start_date", "granularity"),
        Index("idx_acled_agg_country_bucket", "country_id", "bucket_start_date"),
        Index("idx_acled_agg_theater_bucket", "theater", "bucket_start_date"),
        Index("idx_acled_agg_disorder_bucket", "disorder_type", "bucket_start_date"),
        Index(
            "uq_acled_aggregate",
            "bucket_start_date",
            "granularity",
            "country_id",
            "disorder_type",
            unique=True,
        ),
    )
