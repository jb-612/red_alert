from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[int] = mapped_column(Integer, nullable=False)
    category_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    rid: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    matrix_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="csv_backfill")

    __table_args__ = (
        Index("idx_alerts_datetime", "alert_datetime"),
        Index("idx_alerts_category", "category"),
        Index("idx_alerts_location", "location_name"),
        Index("idx_alerts_dedup", "alert_datetime", "location_name", "category", unique=True),
        Index("idx_alerts_loc_cat_dt", "location_name", "category", "alert_datetime"),
    )
