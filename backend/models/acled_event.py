from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class AcledEvent(Base):
    """ACLED conflict event record."""

    __tablename__ = "acled_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id_cnty: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    disorder_type: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    sub_event_type: Mapped[str] = mapped_column(Text, nullable=False)
    actor1: Mapped[str] = mapped_column(Text, nullable=False)
    assoc_actor_1: Mapped[str | None] = mapped_column(Text, nullable=True)
    inter1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor2: Mapped[str | None] = mapped_column(Text, nullable=True)
    assoc_actor_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    inter2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interaction: Mapped[int | None] = mapped_column(Integer, nullable=True)
    civilian_targeting: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    iso: Mapped[int] = mapped_column(Integer, nullable=False)
    region: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin1: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin2: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin3: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    geo_precision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_scale: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    fatalities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    theater: Mapped[str] = mapped_column(String(50), nullable=False, default="core_me")

    __table_args__ = (
        Index("idx_acled_event_date", "event_date"),
        Index("idx_acled_country", "country"),
        Index("idx_acled_event_type", "event_type"),
        Index("idx_acled_actor1", "actor1"),
        Index("idx_acled_geo", "latitude", "longitude"),
        Index("idx_acled_country_date", "country", "event_date"),
        Index("idx_acled_theater", "theater"),
    )
