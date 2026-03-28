from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.alert import Alert


def alert_exists(db: Session, alert_datetime: datetime, location_name: str, category: int) -> bool:
    """Check if an alert with the given key already exists in the database."""
    stmt = select(Alert.id).where(
        Alert.alert_datetime == alert_datetime,
        Alert.location_name == location_name,
        Alert.category == category,
    )
    return db.execute(stmt).first() is not None
