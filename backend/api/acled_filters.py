"""Filter utilities for ACLED conflict event queries."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from backend.models.acled_event import AcledEvent

if TYPE_CHECKING:
    from sqlalchemy import Select


def _apply_acled_date_range(
    stmt: Select,
    from_date: date | None,
    to_date: date | None,
) -> Select:
    """Apply optional date range bounds to the statement."""
    if from_date:
        stmt = stmt.where(AcledEvent.event_date >= from_date)
    if to_date:
        stmt = stmt.where(AcledEvent.event_date <= to_date)
    return stmt


def _apply_acled_entity_filters(
    stmt: Select,
    countries: list[str] | None,
    event_types: list[str] | None,
    sub_event_types: list[str] | None,
    actor: str | None,
    location: str | None,
    theaters: list[str] | None,
) -> Select:
    """Apply country, event type, actor, location, and theater filters."""
    if countries:
        stmt = stmt.where(AcledEvent.country.in_(countries))
    if event_types:
        stmt = stmt.where(AcledEvent.event_type.in_(event_types))
    if sub_event_types:
        stmt = stmt.where(AcledEvent.sub_event_type.in_(sub_event_types))
    if actor:
        stmt = stmt.where(AcledEvent.actor1.contains(actor) | AcledEvent.actor2.contains(actor))
    if location:
        stmt = stmt.where(AcledEvent.location.contains(location))
    if theaters:
        stmt = stmt.where(AcledEvent.theater.in_(theaters))
    return stmt


def apply_acled_filters(
    stmt: Select,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None = None,
    event_types: list[str] | None = None,
    sub_event_types: list[str] | None = None,
    actor: str | None = None,
    location: str | None = None,
    theaters: list[str] | None = None,
) -> Select:
    """Apply date, country, event type, actor, and theater filters to ACLED queries.

    Args:
        stmt: The base SQLAlchemy select statement.
        from_date: Include events on or after this date.
        to_date: Include events on or before this date.
        countries: Optional list of country names to filter by.
        event_types: Optional list of ACLED event types.
        sub_event_types: Optional list of ACLED sub-event types.
        actor: Optional substring match on actor1 or actor2.
        location: Optional substring match on location name.
        theaters: Optional list of theater classifications.

    Returns:
        The filtered select statement.
    """
    stmt = _apply_acled_date_range(stmt, from_date, to_date)
    return _apply_acled_entity_filters(
        stmt, countries, event_types, sub_event_types, actor, location, theaters
    )
