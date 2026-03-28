from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.alert import Alert


def alert_exists(db: Session, alert_datetime: datetime, location_name: str, category: int) -> bool:
    stmt = select(Alert.id).where(
        Alert.alert_datetime == alert_datetime,
        Alert.location_name == location_name,
        Alert.category == category,
    )
    return db.execute(stmt).first() is not None


def bulk_insert_deduped(db: Session, alerts: list[dict]) -> int:
    inserted = 0
    for alert_data in alerts:
        if not alert_exists(
            db,
            alert_data["alert_datetime"],
            alert_data["location_name"],
            alert_data["category"],
        ):
            db.add(Alert(**alert_data))
            inserted += 1
    db.commit()
    return inserted
