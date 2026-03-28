"""Tests for the shared apply_filters function (WI-3.1)."""

from datetime import date, datetime

from backend.api.filters import apply_filters
from sqlalchemy import func, select

from backend.models.alert import Alert


def test_apply_filters_no_filters(db):
    """With no filters, the statement should return all alerts."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="תל אביב", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 1, 2), location_name="חיפה", category=2, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(stmt, from_date=None, to_date=None, categories=None, location=None)
    result = db.scalars(stmt).all()
    assert len(result) == 2


def test_apply_filters_from_date(db):
    """Filters alerts on or after from_date."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="A", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 6, 15), location_name="B", category=1, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(stmt, from_date=date(2024, 3, 1), to_date=None, categories=None, location=None)
    result = db.scalars(stmt).all()
    assert len(result) == 1
    assert result[0].location_name == "B"


def test_apply_filters_to_date(db):
    """Filters alerts on or before to_date."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="A", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 6, 15), location_name="B", category=1, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(stmt, from_date=None, to_date=date(2024, 3, 1), categories=None, location=None)
    result = db.scalars(stmt).all()
    assert len(result) == 1
    assert result[0].location_name == "A"


def test_apply_filters_categories(db):
    """Filters by category list."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="A", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="B", category=2, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="C", category=3, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(stmt, from_date=None, to_date=None, categories=[1, 3], location=None)
    result = db.scalars(stmt).all()
    assert len(result) == 2
    names = {a.location_name for a in result}
    assert names == {"A", "C"}


def test_apply_filters_categories_none_skips_filter(db):
    """When categories is None, all categories are included."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="A", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="B", category=2, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(stmt, from_date=None, to_date=None, categories=None, location=None)
    result = db.scalars(stmt).all()
    assert len(result) == 2


def test_apply_filters_location_substring(db):
    """Filters by location name substring match."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="תל אביב - מרכז", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="תל אביב - יפו", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="חיפה", category=1, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(stmt, from_date=None, to_date=None, categories=None, location="תל אביב")
    result = db.scalars(stmt).all()
    assert len(result) == 2


def test_apply_filters_combined(db):
    """Multiple filters combine with AND logic."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="תל אביב", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 6, 1), location_name="תל אביב", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 6, 1), location_name="חיפה", category=2, source="test"))
    db.commit()

    stmt = select(Alert)
    stmt = apply_filters(
        stmt,
        from_date=date(2024, 3, 1),
        to_date=None,
        categories=[1],
        location="תל אביב",
    )
    result = db.scalars(stmt).all()
    assert len(result) == 1
    assert result[0].alert_datetime.month == 6


def test_apply_filters_with_aggregate(db):
    """apply_filters works with aggregate queries (count)."""
    db.add(Alert(alert_datetime=datetime(2024, 1, 1), location_name="A", category=1, source="test"))
    db.add(Alert(alert_datetime=datetime(2024, 6, 1), location_name="B", category=1, source="test"))
    db.commit()

    stmt = select(func.count()).select_from(Alert)
    stmt = apply_filters(stmt, from_date=date(2024, 3, 1), to_date=None, categories=None, location=None)
    count = db.scalar(stmt)
    assert count == 1
