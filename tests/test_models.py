from datetime import datetime

from backend.models.alert import Alert
from backend.models.category import AlertCategory
from backend.models.location import Location


def test_alert_creation(db):
    alert = Alert(
        alert_datetime=datetime(2023, 10, 7, 6, 30),
        location_name="תל אביב",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="csv_backfill",
    )
    db.add(alert)
    db.commit()

    result = db.query(Alert).first()
    assert result is not None
    assert result.location_name == "תל אביב"
    assert result.category == 1
    assert result.alert_datetime == datetime(2023, 10, 7, 6, 30)


def test_alert_hebrew_text_preserved(db):
    """Hebrew text must survive round-trip to database unchanged."""
    hebrew_name = "באר שבע 288"
    alert = Alert(
        alert_datetime=datetime(2024, 1, 1),
        location_name=hebrew_name,
        category=1,
        source="test",
    )
    db.add(alert)
    db.commit()

    result = db.query(Alert).first()
    assert result.location_name == hebrew_name


def test_location_creation(db):
    loc = Location(
        name="תל אביב",
        name_en="Tel Aviv",
        zone="דן",
        zone_en="Dan",
        latitude=32.0853,
        longitude=34.7818,
    )
    db.add(loc)
    db.commit()

    result = db.query(Location).first()
    assert result.name == "תל אביב"
    assert result.name_en == "Tel Aviv"


def test_category_creation(db):
    cat = AlertCategory(id=1, name_he="ירי רקטות וטילים", name_en="Rocket and missile fire")
    db.add(cat)
    db.commit()

    result = db.query(AlertCategory).first()
    assert result.id == 1
    assert result.name_en == "Rocket and missile fire"


def test_alert_datetime_column_has_timezone():
    """Alert.alert_datetime column should be timezone-aware."""
    col_type = Alert.__table__.c.alert_datetime.type
    assert col_type.timezone is True


def test_dedup_index_prevents_duplicates(db):
    """The unique index on (alert_datetime, location_name, category) must prevent duplicates."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    alert1 = Alert(
        alert_datetime=datetime(2023, 10, 7, 6, 30),
        location_name="תל אביב",
        category=1,
        source="csv_backfill",
    )
    db.add(alert1)
    db.commit()

    alert2 = Alert(
        alert_datetime=datetime(2023, 10, 7, 6, 30),
        location_name="תל אביב",
        category=1,
        source="tzofar",
    )
    db.add(alert2)
    with pytest.raises(IntegrityError):
        db.commit()
