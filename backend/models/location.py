from sqlalchemy import Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    zone: Mapped[str | None] = mapped_column(Text, nullable=True)
    zone_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    countdown_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelter_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
