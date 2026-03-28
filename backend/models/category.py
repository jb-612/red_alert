from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class AlertCategory(Base):
    __tablename__ = "alert_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_he: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
