"""ACLED aggregate API — live conflict pulse endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from datetime import date

from backend.database import get_db
from backend.ingestion.acled_aggregate_client import DISORDER_VARIANTS
from backend.models.acled_aggregate import AcledAggregate
from backend.schemas.acled_aggregate import (
    ConflictPulseResponse,
    PulseBucket,
    PulseCountry,
    PulseTheater,
)

router = APIRouter(prefix="/api/acled/aggregates", tags=["acled-aggregates"])


def _base_filter(granularity: str, disorder_type: str) -> Select:
    return select(AcledAggregate).where(
        AcledAggregate.granularity == granularity,
        AcledAggregate.disorder_type == disorder_type,
    )


def _latest_update(db: Session, granularity: str, disorder_type: str) -> date | None:
    stmt = select(func.max(AcledAggregate.latest_update)).where(
        AcledAggregate.granularity == granularity,
        AcledAggregate.disorder_type == disorder_type,
    )
    return db.scalar(stmt)


def _pulse_timeline(db: Session, granularity: str, disorder_type: str) -> list[PulseBucket]:
    stmt = (
        select(
            AcledAggregate.bucket_start_date.label("bucket"),
            func.sum(AcledAggregate.events).label("events"),
            func.sum(AcledAggregate.fatalities).label("fatalities"),
            func.sum(AcledAggregate.exposure).label("exposure"),
        )
        .where(
            AcledAggregate.granularity == granularity,
            AcledAggregate.disorder_type == disorder_type,
        )
        .group_by(AcledAggregate.bucket_start_date)
        .order_by(AcledAggregate.bucket_start_date)
    )
    return [
        PulseBucket(
            date=str(row.bucket),
            events=int(row.events or 0),
            fatalities=int(row.fatalities or 0),
            exposure=int(row.exposure or 0),
        )
        for row in db.execute(stmt).all()
    ]


def _pulse_top_countries(
    db: Session, granularity: str, disorder_type: str, top_n: int
) -> list[PulseCountry]:
    stmt = (
        select(
            AcledAggregate.country_id,
            AcledAggregate.country_name,
            AcledAggregate.theater,
            func.sum(AcledAggregate.events).label("events"),
            func.sum(AcledAggregate.fatalities).label("fatalities"),
            func.sum(AcledAggregate.exposure).label("exposure"),
        )
        .where(
            AcledAggregate.granularity == granularity,
            AcledAggregate.disorder_type == disorder_type,
        )
        .group_by(
            AcledAggregate.country_id,
            AcledAggregate.country_name,
            AcledAggregate.theater,
        )
        .order_by(func.sum(AcledAggregate.events).desc())
        .limit(top_n)
    )
    return [
        PulseCountry(
            country_id=int(row.country_id),
            country_name=str(row.country_name),
            theater=str(row.theater),
            events=int(row.events or 0),
            fatalities=int(row.fatalities or 0),
            exposure=int(row.exposure or 0),
        )
        for row in db.execute(stmt).all()
    ]


def _row_to_pulse_theater(row: object) -> PulseTheater:
    return PulseTheater(
        theater=str(row.theater),  # type: ignore[attr-defined]
        countries=int(row.countries or 0),  # type: ignore[attr-defined]
        events=int(row.events or 0),  # type: ignore[attr-defined]
        fatalities=int(row.fatalities or 0),  # type: ignore[attr-defined]
        exposure=int(row.exposure or 0),  # type: ignore[attr-defined]
    )


def _pulse_theater_rollup(
    db: Session, granularity: str, disorder_type: str
) -> list[PulseTheater]:
    stmt = (
        select(
            AcledAggregate.theater,
            func.count(func.distinct(AcledAggregate.country_id)).label("countries"),
            func.sum(AcledAggregate.events).label("events"),
            func.sum(AcledAggregate.fatalities).label("fatalities"),
            func.sum(AcledAggregate.exposure).label("exposure"),
        )
        .where(
            AcledAggregate.granularity == granularity,
            AcledAggregate.disorder_type == disorder_type,
        )
        .group_by(AcledAggregate.theater)
        .order_by(func.sum(AcledAggregate.events).desc())
    )
    return [_row_to_pulse_theater(row) for row in db.execute(stmt).all()]


def _window_bounds(timeline: list[PulseBucket]) -> tuple[str | None, str | None]:
    if not timeline:
        return None, None
    return timeline[0].date, timeline[-1].date


def _window_totals(timeline: list[PulseBucket]) -> tuple[int, int, int]:
    events = sum(b.events for b in timeline)
    fatalities = sum(b.fatalities for b in timeline)
    exposure = sum(b.exposure for b in timeline)
    return events, fatalities, exposure


@router.get("/pulse", response_model=ConflictPulseResponse)
def conflict_pulse(
    granularity: str = Query("month", pattern="^(day|month)$"),
    disorder_type: str = Query("all"),
    top_n: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> ConflictPulseResponse:
    """Live global conflict pulse from ACLED pre-computed aggregates.

    Returns a timeline of events/fatalities/exposure, top-N countries by event
    count, and a rollup by conflict theater, all derived from ACLED's Explorer
    overview files. Use `granularity=month` for the 12-month monthly view or
    `granularity=day` for the 29-day daily view. `disorder_type` filters to one
    of ACLED's eight disorder categories (default: 'all').
    """
    if disorder_type not in DISORDER_VARIANTS:
        disorder_type = "all"

    timeline = _pulse_timeline(db, granularity, disorder_type)
    top_countries = _pulse_top_countries(db, granularity, disorder_type, top_n)
    theater_rollup = _pulse_theater_rollup(db, granularity, disorder_type)
    latest = _latest_update(db, granularity, disorder_type)
    window_start, window_end = _window_bounds(timeline)
    total_events, total_fatalities, total_exposure = _window_totals(timeline)

    return ConflictPulseResponse(
        latest_update=str(latest) if latest else None,
        granularity=granularity,
        disorder_type=disorder_type,
        window_start=window_start,
        window_end=window_end,
        total_events=total_events,
        total_fatalities=total_fatalities,
        total_exposure=total_exposure,
        timeline=timeline,
        top_countries=top_countries,
        theater_rollup=theater_rollup,
    )
