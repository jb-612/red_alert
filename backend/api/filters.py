"""Shared query filter logic for alerts endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from backend.models.alert import Alert
from backend.models.location import Location

if TYPE_CHECKING:
    from sqlalchemy import Select


def _apply_date_range(
    stmt: Select,
    from_date: date | None,
    to_date: date | None,
) -> Select:
    """Apply optional date range bounds to the statement."""
    if from_date:
        stmt = stmt.where(Alert.alert_datetime >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(Alert.alert_datetime <= datetime.combine(to_date, datetime.max.time()))
    return stmt


def apply_filters(
    stmt: Select,
    from_date: date | None,
    to_date: date | None,
    categories: list[int] | None = None,
    location: str | None = None,
    zone: str | None = None,
) -> Select:
    """Apply date, category, location, and zone filters to a SQLAlchemy select.

    Args:
        stmt: The base SQLAlchemy select statement.
        from_date: Include alerts on or after this date.
        to_date: Include alerts on or before this date.
        categories: Optional list of category IDs to filter by.
        location: Optional substring match on location_name (max 200 chars).
        zone: Optional zone_en filter (limits to locations in the given zone).

    Returns:
        The filtered select statement.
    """
    stmt = _apply_date_range(stmt, from_date, to_date)
    if categories:
        stmt = stmt.where(Alert.category.in_(categories))
    if location:
        stmt = stmt.where(Alert.location_name.contains(location[:200]))
    if zone:
        zone_names = select(Location.name).where(Location.zone_en == zone)
        stmt = stmt.where(Alert.location_name.in_(zone_names))
    return stmt
