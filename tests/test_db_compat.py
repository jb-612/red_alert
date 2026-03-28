"""Tests for backend.db_compat — dialect-aware SQL expression builders."""

from __future__ import annotations

from datetime import datetime

from backend.db_compat import (
    extract_date,
    extract_dow,
    extract_hour,
    extract_month,
    extract_week,
)
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from backend.models.alert import Alert


def _seed_alert(db: Session, dt: datetime) -> Alert:
    """Insert a single alert with the given datetime and return it."""
    alert = Alert(
        alert_datetime=dt,
        location_name="תל אביב",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    )
    db.add(alert)
    db.commit()
    return alert


def test_extract_date_format(db: Session) -> None:
    """extract_date returns YYYY-MM-DD string."""
    _seed_alert(db, datetime(2023, 10, 7, 6, 30))
    result = db.scalar(select(extract_date(Alert.alert_datetime)))
    assert result == "2023-10-07"


def test_extract_date_multiple_rows(db: Session) -> None:
    """extract_date works as a group-by key across multiple alerts."""
    _seed_alert(db, datetime(2023, 10, 7, 6, 30))
    _seed_alert(db, datetime(2023, 10, 7, 14, 0))
    _seed_alert(db, datetime(2023, 10, 8, 9, 0))

    stmt = (
        select(extract_date(Alert.alert_datetime).label("day"), func.count().label("cnt"))
        .group_by("day")
        .order_by("day")
    )
    rows = db.execute(stmt).all()
    assert len(rows) == 2
    assert rows[0].day == "2023-10-07"
    assert rows[0].cnt == 2
    assert rows[1].day == "2023-10-08"
    assert rows[1].cnt == 1


def test_extract_hour_format(db: Session) -> None:
    """extract_hour returns two-digit hour string (e.g. '06')."""
    _seed_alert(db, datetime(2023, 10, 7, 6, 30))
    result = db.scalar(select(extract_hour(Alert.alert_datetime)))
    assert result == "06"


def test_extract_hour_midnight(db: Session) -> None:
    """extract_hour returns '00' for midnight."""
    _seed_alert(db, datetime(2023, 10, 7, 0, 5))
    result = db.scalar(select(extract_hour(Alert.alert_datetime)))
    assert result == "00"


def test_extract_hour_cast_to_integer(db: Session) -> None:
    """extract_hour result can be cast to Integer for numeric comparisons."""
    _seed_alert(db, datetime(2023, 10, 7, 22, 15))
    result = db.scalar(select(cast(extract_hour(Alert.alert_datetime), Integer)))
    assert result == 22


def test_extract_dow_sunday(db: Session) -> None:
    """extract_dow returns '0' for Sunday (SQLite %w convention)."""
    # 2023-10-08 is a Sunday
    _seed_alert(db, datetime(2023, 10, 8, 10, 0))
    result = db.scalar(select(extract_dow(Alert.alert_datetime)))
    assert result == "0"


def test_extract_dow_saturday(db: Session) -> None:
    """extract_dow returns '6' for Saturday."""
    # 2023-10-07 is a Saturday
    _seed_alert(db, datetime(2023, 10, 7, 10, 0))
    result = db.scalar(select(extract_dow(Alert.alert_datetime)))
    assert result == "6"


def test_extract_dow_cast_to_integer(db: Session) -> None:
    """extract_dow result can be cast to Integer for numeric operations."""
    # 2023-10-09 is a Monday = %w returns 1
    _seed_alert(db, datetime(2023, 10, 9, 10, 0))
    result = db.scalar(select(cast(extract_dow(Alert.alert_datetime), Integer)))
    assert result == 1


def test_extract_week_format(db: Session) -> None:
    """extract_week returns YYYY-WNN string."""
    _seed_alert(db, datetime(2023, 10, 7, 6, 30))
    result = db.scalar(select(extract_week(Alert.alert_datetime)))
    assert result is not None
    assert result.startswith("2023-W")
    # The format should be YYYY-WNN where NN is zero-padded
    parts = result.split("-W")
    assert len(parts) == 2
    assert len(parts[1]) == 2


def test_extract_week_group_by(db: Session) -> None:
    """extract_week groups alerts from the same week together."""
    # Mon Oct 9 and Wed Oct 11 are the same week
    _seed_alert(db, datetime(2023, 10, 9, 10, 0))
    _seed_alert(db, datetime(2023, 10, 11, 10, 0))
    # Mon Oct 16 is the next week
    _seed_alert(db, datetime(2023, 10, 16, 10, 0))

    stmt = (
        select(extract_week(Alert.alert_datetime).label("wk"), func.count().label("cnt"))
        .group_by("wk")
        .order_by("wk")
    )
    rows = db.execute(stmt).all()
    assert len(rows) == 2
    assert rows[0].cnt == 2
    assert rows[1].cnt == 1


def test_extract_month_format(db: Session) -> None:
    """extract_month returns YYYY-MM string."""
    _seed_alert(db, datetime(2023, 10, 7, 6, 30))
    result = db.scalar(select(extract_month(Alert.alert_datetime)))
    assert result == "2023-10"


def test_extract_month_group_by(db: Session) -> None:
    """extract_month groups alerts from the same month together."""
    _seed_alert(db, datetime(2023, 10, 1, 10, 0))
    _seed_alert(db, datetime(2023, 10, 31, 10, 0))
    _seed_alert(db, datetime(2023, 11, 1, 10, 0))

    stmt = (
        select(extract_month(Alert.alert_datetime).label("mo"), func.count().label("cnt"))
        .group_by("mo")
        .order_by("mo")
    )
    rows = db.execute(stmt).all()
    assert len(rows) == 2
    assert rows[0].mo == "2023-10"
    assert rows[0].cnt == 2
    assert rows[1].mo == "2023-11"
    assert rows[1].cnt == 1


def test_extract_month_january_zero_padded(db: Session) -> None:
    """extract_month zero-pads single-digit months (e.g. '01' not '1')."""
    _seed_alert(db, datetime(2024, 1, 15, 10, 0))
    result = db.scalar(select(extract_month(Alert.alert_datetime)))
    assert result == "2024-01"
