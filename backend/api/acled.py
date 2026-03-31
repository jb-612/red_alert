"""ACLED conflict event API endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.acled_filters import apply_acled_filters
from backend.database import get_db
from backend.db_compat import extract_date, extract_month, extract_week
from backend.models.acled_event import AcledEvent
from backend.models.sync_state import SyncState
from backend.schemas.acled import (
    AcledActorCount,
    AcledCountryCount,
    AcledEventListResponse,
    AcledEventResponse,
    AcledEventTypeCount,
    AcledGeoPoint,
    AcledSyncStatus,
    AcledTheaterCount,
    AcledTimelineBucket,
    AcledTimelineResponse,
)

router = APIRouter(prefix="/api/acled", tags=["acled"])


@router.get("", response_model=AcledEventListResponse)
def list_acled_events(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    event_types: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AcledEventListResponse:
    """List ACLED conflict events with filtering and pagination."""
    base = select(AcledEvent)
    base = apply_acled_filters(
        base, from_date, to_date, countries, event_types, actor=actor, theaters=theaters
    )

    total = db.scalar(select(func.count()).select_from(base.subquery()))
    items = db.scalars(
        base.order_by(AcledEvent.event_date.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    return AcledEventListResponse(
        items=[AcledEventResponse.model_validate(e) for e in items],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/geo", response_model=list[AcledGeoPoint])
def acled_geo(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    event_types: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
) -> list[AcledGeoPoint]:
    """Aggregated ACLED event data per location for the map."""
    stmt = (
        select(
            AcledEvent.location,
            AcledEvent.country,
            AcledEvent.latitude,
            AcledEvent.longitude,
            func.count().label("count"),
            func.sum(AcledEvent.fatalities).label("fatalities"),
        )
        .group_by(AcledEvent.location, AcledEvent.country, AcledEvent.latitude, AcledEvent.longitude)
    )
    stmt = apply_acled_filters(
        stmt, from_date, to_date, countries, event_types, actor=actor, theaters=theaters
    )

    rows = db.execute(stmt).all()
    return [
        AcledGeoPoint(
            location=r.location,
            country=r.country,
            lat=float(r.latitude),
            lng=float(r.longitude),
            count=r.count,
            fatalities=r.fatalities or 0,
            event_types=[],
        )
        for r in rows
    ]


@router.get("/timeline", response_model=AcledTimelineResponse)
def acled_timeline(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    event_types: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
) -> AcledTimelineResponse:
    """Timeline of ACLED events bucketed by day, week, or month."""
    period_expr = extract_date(AcledEvent.event_date)
    if granularity == "week":
        period_expr = extract_week(AcledEvent.event_date)
    elif granularity == "month":
        period_expr = extract_month(AcledEvent.event_date)

    stmt = (
        select(
            period_expr.label("period"),
            func.count().label("count"),
            func.sum(AcledEvent.fatalities).label("fatalities"),
        )
        .group_by("period")
    )
    stmt = apply_acled_filters(
        stmt, from_date, to_date, countries, event_types, actor=actor, theaters=theaters
    )
    stmt = stmt.order_by("period")

    rows = db.execute(stmt).all()
    buckets = [
        AcledTimelineBucket(period=str(r.period), count=r.count, fatalities=r.fatalities or 0)
        for r in rows
    ]
    return AcledTimelineResponse(buckets=buckets, granularity=granularity)


@router.get("/by-country", response_model=list[AcledCountryCount])
def acled_by_country(
    from_date: date | None = None,
    to_date: date | None = None,
    event_types: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
) -> list[AcledCountryCount]:
    """Event counts grouped by country."""
    stmt = (
        select(
            AcledEvent.country,
            func.count().label("count"),
            func.sum(AcledEvent.fatalities).label("fatalities"),
        )
        .group_by(AcledEvent.country)
    )
    stmt = apply_acled_filters(
        stmt, from_date, to_date, event_types=event_types, actor=actor, theaters=theaters
    )
    stmt = stmt.order_by(func.count().desc())

    rows = db.execute(stmt).all()
    return [
        AcledCountryCount(country=r.country, count=r.count, fatalities=r.fatalities or 0)
        for r in rows
    ]


@router.get("/by-type", response_model=list[AcledEventTypeCount])
def acled_by_type(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
) -> list[AcledEventTypeCount]:
    """Event counts grouped by event type and sub-event type."""
    stmt = (
        select(
            AcledEvent.event_type,
            AcledEvent.sub_event_type,
            func.count().label("count"),
            func.sum(AcledEvent.fatalities).label("fatalities"),
        )
        .group_by(AcledEvent.event_type, AcledEvent.sub_event_type)
    )
    stmt = apply_acled_filters(
        stmt, from_date, to_date, countries, actor=actor, theaters=theaters
    )
    stmt = stmt.order_by(func.count().desc())

    rows = db.execute(stmt).all()
    return [
        AcledEventTypeCount(
            event_type=r.event_type,
            sub_event_type=r.sub_event_type,
            count=r.count,
            fatalities=r.fatalities or 0,
        )
        for r in rows
    ]


@router.get("/by-actor", response_model=list[AcledActorCount])
def acled_by_actor(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    event_types: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[AcledActorCount]:
    """Event counts grouped by primary actor."""
    stmt = (
        select(
            AcledEvent.actor1.label("actor"),
            func.count().label("count"),
            func.sum(AcledEvent.fatalities).label("fatalities"),
        )
        .group_by(AcledEvent.actor1)
    )
    stmt = apply_acled_filters(
        stmt, from_date, to_date, countries, event_types, theaters=theaters
    )
    stmt = stmt.order_by(func.count().desc()).limit(limit)

    rows = db.execute(stmt).all()
    return [
        AcledActorCount(actor=r.actor, count=r.count, fatalities=r.fatalities or 0)
        for r in rows
    ]


@router.get("/by-theater", response_model=list[AcledTheaterCount])
def acled_by_theater(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    event_types: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
) -> list[AcledTheaterCount]:
    """Event counts grouped by conflict theater."""
    stmt = (
        select(
            AcledEvent.theater,
            func.count().label("count"),
            func.sum(AcledEvent.fatalities).label("fatalities"),
        )
        .group_by(AcledEvent.theater)
    )
    stmt = apply_acled_filters(
        stmt, from_date, to_date, countries, event_types, actor=actor
    )
    stmt = stmt.order_by(func.count().desc())

    rows = db.execute(stmt).all()
    return [
        AcledTheaterCount(theater=r.theater, count=r.count, fatalities=r.fatalities or 0)
        for r in rows
    ]


@router.get("/sync-status", response_model=AcledSyncStatus)
def acled_sync_status(db: Session = Depends(get_db)) -> AcledSyncStatus:
    """Current ACLED sync state."""
    state = db.scalar(select(SyncState).where(SyncState.source == "acled"))
    total = db.scalar(select(func.count()).select_from(AcledEvent)) or 0

    return AcledSyncStatus(
        last_sync_date=str(state.last_sync_date) if state and state.last_sync_date else None,
        last_sync_at=state.last_sync_at.isoformat() if state and state.last_sync_at else None,
        total_events=total,
    )
