from datetime import datetime

from backend.ingestion.deduplication import alert_exists, bulk_insert_deduped
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


def test_bulk_insert_deduped_inserts_new(db):
    alerts = [
        {
            "alert_datetime": datetime(2024, 1, 1),
            "location_name": "תל אביב",
            "category": 1,
            "source": "test",
        },
        {
            "alert_datetime": datetime(2024, 1, 1),
            "location_name": "חיפה",
            "category": 1,
            "source": "test",
        },
    ]
    inserted = bulk_insert_deduped(db, alerts)
    assert inserted == 2
    assert db.query(Alert).count() == 2


def test_bulk_insert_deduped_skips_existing(db):
    db.add(
        Alert(
            alert_datetime=datetime(2024, 1, 1),
            location_name="תל אביב",
            category=1,
            source="test",
        )
    )
    db.commit()

    alerts = [
        {
            "alert_datetime": datetime(2024, 1, 1),
            "location_name": "תל אביב",
            "category": 1,
            "source": "test",
        },
        {
            "alert_datetime": datetime(2024, 1, 1),
            "location_name": "חיפה",
            "category": 1,
            "source": "test",
        },
    ]
    inserted = bulk_insert_deduped(db, alerts)
    assert inserted == 1
    assert db.query(Alert).count() == 2
