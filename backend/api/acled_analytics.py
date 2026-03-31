"""ACLED conflict analytics endpoints — anomalies, escalation, actor profiles."""

from __future__ import annotations

import statistics
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from backend.api.acled_filters import apply_acled_filters
from backend.database import get_db
from backend.db_compat import extract_date, extract_month, extract_week
from backend.models.acled_event import AcledEvent
from backend.schemas.acled import (
    AcledActorProfile,
    AcledAnomalyDay,
    AcledAnomalyResponse,
    AcledCivilianCountryImpact,
    AcledCivilianImpactResponse,
    AcledEscalationEntry,
    AcledEscalationResponse,
    AcledTheaterSeries,
    AcledTheaterTimelineResponse,
    AcledTimelineBucket,
)

router = APIRouter(prefix="/api/acled", tags=["acled-analytics"])


# --- Anomaly Detection ---


def _query_acled_daily(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
    actor: str | None,
) -> list[tuple[str, int, int]]:
    """Query daily event counts and fatalities for ACLED."""
    stmt = select(
        extract_date(AcledEvent.event_date).label("day"),
        func.count().label("count"),
        func.sum(AcledEvent.fatalities).label("fatalities"),
    ).group_by("day").order_by("day")
    stmt = apply_acled_filters(stmt, from_date, to_date, countries, actor=actor, theaters=theaters)
    rows = db.execute(stmt).all()
    return [(str(r[0]), int(r[1]), int(r[2] or 0)) for r in rows]


def _compute_acled_anomalies(
    daily: list[tuple[str, int, int]], threshold: float, limit: int
) -> AcledAnomalyResponse:
    """Compute z-score anomalies from daily counts."""
    if len(daily) < 2:
        return AcledAnomalyResponse(
            mean_daily_count=0.0, std_daily_count=0.0,
            threshold=threshold, total_days_analyzed=len(daily), anomalies=[],
        )

    counts = [c for _, c, _ in daily]
    mu = statistics.mean(counts)
    sigma = statistics.stdev(counts)

    if sigma == 0:
        return AcledAnomalyResponse(
            mean_daily_count=round(mu, 2), std_daily_count=0.0,
            threshold=threshold, total_days_analyzed=len(daily), anomalies=[],
        )

    anomalies = _find_acled_anomalies(daily, mu, sigma, threshold)
    anomalies.sort(key=lambda a: abs(a.z_score), reverse=True)

    return AcledAnomalyResponse(
        mean_daily_count=round(mu, 2), std_daily_count=round(sigma, 2),
        threshold=threshold, total_days_analyzed=len(daily),
        anomalies=anomalies[:limit],
    )


def _find_acled_anomalies(
    daily: list[tuple[str, int, int]], mu: float, sigma: float, threshold: float
) -> list[AcledAnomalyDay]:
    """Filter daily counts to those exceeding z-score threshold."""
    result: list[AcledAnomalyDay] = []
    for day, count, fatalities in daily:
        z = (count - mu) / sigma
        if abs(z) > threshold:
            result.append(AcledAnomalyDay(
                date=day, count=count, fatalities=fatalities,
                z_score=round(z, 2), direction="high" if z > 0 else "low",
            ))
    return result


@router.get("/anomalies", response_model=AcledAnomalyResponse)
def acled_anomalies(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    threshold: float = Query(2.0, ge=1.0, le=4.0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AcledAnomalyResponse:
    """Detect anomalous days using z-score on daily ACLED event counts."""
    daily = _query_acled_daily(db, from_date, to_date, countries, theaters, actor)
    return _compute_acled_anomalies(daily, threshold, limit)


# --- Escalation Tracker ---


def _get_week_counts(
    db: Session, start: date, end: date
) -> dict[str, tuple[int, int]]:
    """Get event count and fatalities per theater for a date range."""
    stmt = select(
        AcledEvent.theater,
        func.count().label("count"),
        func.sum(AcledEvent.fatalities).label("fatalities"),
    ).where(
        AcledEvent.event_date >= start,
        AcledEvent.event_date <= end,
    ).group_by(AcledEvent.theater)
    rows = db.execute(stmt).all()
    return {str(r[0]): (int(r[1]), int(r[2] or 0)) for r in rows}


@router.get("/escalation", response_model=AcledEscalationResponse)
def acled_escalation(
    db: Session = Depends(get_db),
) -> AcledEscalationResponse:
    """Week-over-week escalation by theater."""
    max_date = db.scalar(select(func.max(AcledEvent.event_date)))
    if not max_date:
        return AcledEscalationResponse(theaters=[], period_end="")

    current_end = max_date
    current_start = current_end - timedelta(days=6)
    prev_end = current_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)

    current = _get_week_counts(db, current_start, current_end)
    previous = _get_week_counts(db, prev_start, prev_end)

    all_theaters = sorted(set(list(current.keys()) + list(previous.keys())))
    entries = []
    for theater in all_theaters:
        cur_count, cur_fat = current.get(theater, (0, 0))
        prev_count, _ = previous.get(theater, (0, 0))
        pct = round((cur_count - prev_count) / prev_count * 100, 1) if prev_count > 0 else None
        entries.append(AcledEscalationEntry(
            theater=theater, current_week_count=cur_count,
            previous_week_count=prev_count, change_pct=pct,
            fatalities_current=cur_fat,
        ))

    return AcledEscalationResponse(
        theaters=entries, period_end=str(current_end),
    )


# --- Actor Profile ---


@router.get("/actor-profile", response_model=AcledActorProfile)
def acled_actor_profile(
    actor: str = Query(..., max_length=200),
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
) -> AcledActorProfile:
    """Intelligence profile for a single actor."""
    base = select(AcledEvent).where(
        AcledEvent.actor1.contains(actor) | AcledEvent.actor2.contains(actor)
    )
    base = apply_acled_filters(base, from_date, to_date)
    sub = base.subquery()

    total = db.scalar(select(func.count()).select_from(sub)) or 0
    fatalities = db.scalar(select(func.sum(sub.c.fatalities)).select_from(sub)) or 0
    countries = [r[0] for r in db.execute(select(distinct(sub.c.country))).all()]
    event_types = [r[0] for r in db.execute(select(distinct(sub.c.event_type))).all()]
    theaters = [r[0] for r in db.execute(select(distinct(sub.c.theater))).all()]

    return AcledActorProfile(
        actor=actor, total_events=total, total_fatalities=fatalities,
        countries=countries, event_types=event_types, theaters=theaters,
    )


# --- Theater Timeline ---


@router.get("/theater-timeline", response_model=AcledTheaterTimelineResponse)
def acled_theater_timeline(
    from_date: date | None = None,
    to_date: date | None = None,
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
) -> AcledTheaterTimelineResponse:
    """Multi-series timeline with one series per theater."""
    period_expr = extract_date(AcledEvent.event_date)
    if granularity == "week":
        period_expr = extract_week(AcledEvent.event_date)
    elif granularity == "month":
        period_expr = extract_month(AcledEvent.event_date)

    stmt = select(
        AcledEvent.theater,
        period_expr.label("period"),
        func.count().label("count"),
        func.sum(AcledEvent.fatalities).label("fatalities"),
    ).group_by(AcledEvent.theater, "period").order_by("period")
    stmt = apply_acled_filters(stmt, from_date, to_date)

    rows = db.execute(stmt).all()

    series_map: dict[str, list[AcledTimelineBucket]] = {}
    for r in rows:
        theater = r.theater
        if theater not in series_map:
            series_map[theater] = []
        series_map[theater].append(
            AcledTimelineBucket(period=str(r.period), count=r.count, fatalities=r.fatalities or 0)
        )

    series = [AcledTheaterSeries(theater=t, buckets=b) for t, b in sorted(series_map.items())]
    return AcledTheaterTimelineResponse(series=series, granularity=granularity)


# --- Civilian Impact ---


@router.get("/civilian-impact", response_model=AcledCivilianImpactResponse)
def acled_civilian_impact(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    db: Session = Depends(get_db),
) -> AcledCivilianImpactResponse:
    """Civilian impact analysis — events with civilian targeting."""
    base = select(AcledEvent).where(
        AcledEvent.civilian_targeting.isnot(None),
        AcledEvent.civilian_targeting != "",
    )
    base = apply_acled_filters(base, from_date, to_date, countries, theaters=theaters)
    sub = base.subquery()

    total_events = db.scalar(select(func.count()).select_from(sub)) or 0
    total_fatalities = db.scalar(select(func.sum(sub.c.fatalities)).select_from(sub)) or 0

    by_country_stmt = select(
        sub.c.country,
        func.count().label("civilian_events"),
        func.sum(sub.c.fatalities).label("civilian_fatalities"),
    ).group_by(sub.c.country).order_by(func.count().desc())

    by_country = [
        AcledCivilianCountryImpact(
            country=r.country, civilian_events=r.civilian_events,
            civilian_fatalities=r.civilian_fatalities or 0,
        )
        for r in db.execute(by_country_stmt).all()
    ]

    return AcledCivilianImpactResponse(
        total_civilian_events=total_events,
        total_civilian_fatalities=total_fatalities,
        by_country=by_country,
    )
