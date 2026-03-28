from datetime import datetime

from backend.ingestion.deduplication import alert_exists
from backend.models.alert import Alert


def test_alert_exists_returns_false_when_empty(db):
    assert alert_exists(db, datetime(2024, 1, 1), "תל אביב", 1) is False


def test_alert_exists_returns_true_after_insert(db):
    db.add(
        Alert(
            alert_datetime=datetime(2024, 1, 1),
            location_name="תל אביב",
            category=1,
            source="test",
        )
    )
    db.commit()
    assert alert_exists(db, datetime(2024, 1, 1), "תל אביב", 1) is True


def test_alert_exists_different_category_returns_false(db):
    db.add(
        Alert(
            alert_datetime=datetime(2024, 1, 1),
            location_name="תל אביב",
            category=1,
            source="test",
        )
    )
    db.commit()
    assert alert_exists(db, datetime(2024, 1, 1), "תל אביב", 13) is False
