"""Shared query filter logic for alerts endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from backend.models.alert import Alert

if TYPE_CHECKING:
    from sqlalchemy import Select


def apply_filters(
    stmt: Select,
    from_date: date | None,
    to_date: date | None,
    categories: list[int] | None = None,
    location: str | None = None,
) -> Select:
    """Apply date, category, and location filters to a SQLAlchemy select.

    Args:
        stmt: The base SQLAlchemy select statement.
        from_date: Include alerts on or after this date.
        to_date: Include alerts on or before this date.
        categories: Optional list of category IDs to filter by.
        location: Optional substring match on location_name (max 200 chars).

    Returns:
        The filtered select statement.
    """
    if from_date:
        stmt = stmt.where(Alert.alert_datetime >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(Alert.alert_datetime <= datetime.combine(to_date, datetime.max.time()))
    if categories:
        stmt = stmt.where(Alert.category.in_(categories))
    if location:
        stmt = stmt.where(Alert.location_name.contains(location[:200]))
    return stmt
