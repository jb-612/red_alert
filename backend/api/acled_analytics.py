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
    AcledCountryEventTypeCell,
    AcledCountryMatrixEntry,
    AcledCountryMatrixResponse,
    AcledEscalationEntry,
    AcledEscalationResponse,
    AcledSituationResponse,
    AcledTheaterSeries,
    AcledTheaterTimelineResponse,
    AcledTimelineBucket,
    AcledTopActorEntry,
    AcledTopActorsResponse,
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


# --- Situation Summary ---

_CONFLICT_START = date(2026, 2, 28)


def _situation_totals(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
    actor: str | None,
) -> tuple[int, int]:
    """Return (total_events, total_fatalities) for the filter range."""
    stmt = select(
        func.count().label("cnt"),
        func.coalesce(func.sum(AcledEvent.fatalities), 0).label("fat"),
    )
    stmt = apply_acled_filters(stmt, from_date, to_date, countries, actor=actor, theaters=theaters)
    row = db.execute(stmt).one()
    return int(row.cnt), int(row.fat)


def _situation_7d_counts(
    db: Session,
    ref_date: date,
    countries: list[str] | None,
    theaters: list[str] | None,
    actor: str | None,
) -> tuple[int, int, int, int]:
    """Return (events_last_7d, events_prior_7d, fat_last_7d, fat_prior_7d)."""
    last_start = ref_date - timedelta(days=6)
    prior_end = last_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=6)

    stmt_last = select(
        func.count(), func.coalesce(func.sum(AcledEvent.fatalities), 0),
    )
    stmt_last = apply_acled_filters(
        stmt_last, last_start, ref_date, countries, actor=actor, theaters=theaters,
    )
    r_last = db.execute(stmt_last).one()

    stmt_prior = select(
        func.count(), func.coalesce(func.sum(AcledEvent.fatalities), 0),
    )
    stmt_prior = apply_acled_filters(
        stmt_prior, prior_start, prior_end, countries, actor=actor, theaters=theaters,
    )
    r_prior = db.execute(stmt_prior).one()

    return int(r_last[0]), int(r_prior[0]), int(r_last[1]), int(r_prior[1])


def _situation_distinct_counts(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
    actor: str | None,
) -> tuple[int, int]:
    """Return (active_theaters, active_countries)."""
    base = select(AcledEvent)
    base = apply_acled_filters(base, from_date, to_date, countries, actor=actor, theaters=theaters)
    sub = base.subquery()

    n_theaters = db.scalar(select(func.count(distinct(sub.c.theater)))) or 0
    n_countries = db.scalar(select(func.count(distinct(sub.c.country)))) or 0
    return int(n_theaters), int(n_countries)


def _top_escalating_theater(
    db: Session,
    ref_date: date,
) -> str | None:
    """Theater with highest week-over-week % increase."""
    current = _get_week_counts(db, ref_date - timedelta(days=6), ref_date)
    prev_end = ref_date - timedelta(days=7)
    previous = _get_week_counts(db, prev_end - timedelta(days=6), prev_end)

    best_theater: str | None = None
    best_pct: float = -1.0
    for theater, (cur_count, _) in current.items():
        prev_count = previous.get(theater, (0, 0))[0]
        if prev_count > 0:
            pct = (cur_count - prev_count) / prev_count * 100
            if pct > best_pct:
                best_pct = pct
                best_theater = theater
    return best_theater


def _build_situation(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
    actor: str | None,
) -> AcledSituationResponse:
    """Assemble situation response from component queries."""
    total_events, total_fat = _situation_totals(
        db, from_date, to_date, countries, theaters, actor,
    )

    if total_events == 0:
        return AcledSituationResponse(
            total_events=0, total_fatalities=0,
            events_last_7d=0, events_prior_7d=0, trend_pct=None,
            fatalities_last_7d=0, fatalities_prior_7d=0,
            active_theaters=0, active_countries=0,
            top_escalating_theater=None, last_event_date=None,
            conflict_day_number=0,
        )

    ref_date = to_date or db.scalar(select(func.max(AcledEvent.event_date))) or date.today()
    ev7, ev_prev, fat7, fat_prev = _situation_7d_counts(
        db, ref_date, countries, theaters, actor,
    )
    trend = round((ev7 - ev_prev) / ev_prev * 100, 1) if ev_prev > 0 else None

    n_theaters, n_countries = _situation_distinct_counts(
        db, from_date, to_date, countries, theaters, actor,
    )

    last_date_stmt = select(func.max(AcledEvent.event_date))
    last_date_stmt = apply_acled_filters(
        last_date_stmt, from_date, to_date, countries, actor=actor, theaters=theaters,
    )
    last_event = db.scalar(last_date_stmt)
    last_event_str = str(last_event) if last_event else None

    first_date_stmt = select(func.min(AcledEvent.event_date))
    first_date_stmt = apply_acled_filters(
        first_date_stmt, from_date, to_date, countries, actor=actor, theaters=theaters,
    )
    first_event = db.scalar(first_date_stmt)
    origin = min(_CONFLICT_START, first_event) if first_event else _CONFLICT_START
    day_num = (ref_date - origin).days

    return AcledSituationResponse(
        total_events=total_events, total_fatalities=total_fat,
        events_last_7d=ev7, events_prior_7d=ev_prev, trend_pct=trend,
        fatalities_last_7d=fat7, fatalities_prior_7d=fat_prev,
        active_theaters=n_theaters, active_countries=n_countries,
        top_escalating_theater=_top_escalating_theater(db, ref_date),
        last_event_date=last_event_str,
        conflict_day_number=day_num,
    )


@router.get("/situation", response_model=AcledSituationResponse)
def acled_situation(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
) -> AcledSituationResponse:
    """Conflict situation summary with 7-day trends and key metrics."""
    return _build_situation(db, from_date, to_date, countries, theaters, actor)


# --- Top Actors ---


def _query_top_actors(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
    limit: int,
) -> list[tuple[str, int, int]]:
    """Return top actors by event count: (actor, events, fatalities)."""
    stmt = select(
        AcledEvent.actor1,
        func.count().label("cnt"),
        func.coalesce(func.sum(AcledEvent.fatalities), 0).label("fat"),
    ).group_by(AcledEvent.actor1).order_by(func.count().desc()).limit(limit)
    stmt = apply_acled_filters(stmt, from_date, to_date, countries, theaters=theaters)
    return [(str(r[0]), int(r[1]), int(r[2])) for r in db.execute(stmt).all()]


def _actor_details(
    db: Session,
    actor_name: str,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
) -> tuple[list[str], str | None, int]:
    """Return (countries, primary_theater, events_last_7d) for an actor."""
    base = select(AcledEvent).where(AcledEvent.actor1 == actor_name)
    base = apply_acled_filters(base, from_date, to_date, countries, theaters=theaters)
    sub = base.subquery()

    actor_countries = [
        r[0] for r in db.execute(select(distinct(sub.c.country))).all()
    ]

    theater_row = db.execute(
        select(sub.c.theater, func.count().label("cnt"))
        .group_by(sub.c.theater)
        .order_by(func.count().desc())
        .limit(1),
    ).first()
    primary_theater = str(theater_row[0]) if theater_row else None

    ref = to_date or db.scalar(select(func.max(AcledEvent.event_date))) or date.today()
    week_start = ref - timedelta(days=6)
    recent_stmt = select(func.count()).where(
        AcledEvent.actor1 == actor_name,
        AcledEvent.event_date >= week_start,
        AcledEvent.event_date <= ref,
    )
    recent_stmt = apply_acled_filters(
        recent_stmt, from_date=week_start, to_date=ref, countries=countries, theaters=theaters,
    )
    ev7 = db.scalar(recent_stmt) or 0

    return actor_countries, primary_theater, int(ev7)


def _build_actor_entry(
    db: Session,
    actor_name: str,
    total_events: int,
    total_fatalities: int,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
) -> AcledTopActorEntry:
    """Build a single AcledTopActorEntry."""
    lethality = round(total_fatalities / total_events, 2) if total_events > 0 else 0.0
    actor_countries, primary_theater, ev7 = _actor_details(
        db, actor_name, from_date, to_date, countries, theaters,
    )
    return AcledTopActorEntry(
        actor=actor_name,
        total_events=total_events,
        total_fatalities=total_fatalities,
        lethality=lethality,
        countries=actor_countries,
        primary_theater=primary_theater,
        events_last_7d=ev7,
    )


@router.get("/top-actors", response_model=AcledTopActorsResponse)
def acled_top_actors(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> AcledTopActorsResponse:
    """Top actors ranked by event count with lethality and sparkline data."""
    raw = _query_top_actors(db, from_date, to_date, countries, theaters, limit)
    actors = [
        _build_actor_entry(db, name, cnt, fat, from_date, to_date, countries, theaters)
        for name, cnt, fat in raw
    ]
    return AcledTopActorsResponse(actors=actors)


# --- Country × Event Type Matrix ---


def _query_country_event_matrix(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    countries: list[str] | None,
    theaters: list[str] | None,
    actor: str | None,
) -> list[tuple[str, str, int, int]]:
    """Return (country, event_type, count, fatalities) rows."""
    stmt = select(
        AcledEvent.country,
        AcledEvent.event_type,
        func.count().label("cnt"),
        func.coalesce(func.sum(AcledEvent.fatalities), 0).label("fat"),
    ).group_by(AcledEvent.country, AcledEvent.event_type).order_by(AcledEvent.country)
    stmt = apply_acled_filters(stmt, from_date, to_date, countries, actor=actor, theaters=theaters)
    return [
        (str(r[0]), str(r[1]), int(r[2]), int(r[3]))
        for r in db.execute(stmt).all()
    ]


def _build_country_matrix(
    rows: list[tuple[str, str, int, int]],
) -> list[AcledCountryMatrixEntry]:
    """Pivot flat rows into country → {event_type: {count, fatalities}}."""
    country_map: dict[str, dict[str, AcledCountryEventTypeCell]] = {}
    for country, event_type, count, fatalities in rows:
        if country not in country_map:
            country_map[country] = {}
        country_map[country][event_type] = AcledCountryEventTypeCell(
            count=count, fatalities=fatalities,
        )
    return [
        AcledCountryMatrixEntry(country=c, event_types=et)
        for c, et in sorted(country_map.items())
    ]


@router.get("/country-matrix", response_model=AcledCountryMatrixResponse)
def acled_country_matrix(
    from_date: date | None = None,
    to_date: date | None = None,
    countries: list[str] | None = Query(None),
    theaters: list[str] | None = Query(None),
    actor: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
) -> AcledCountryMatrixResponse:
    """Country × Event Type matrix with counts and fatalities."""
    rows = _query_country_event_matrix(
        db, from_date, to_date, countries, theaters, actor,
    )
    return AcledCountryMatrixResponse(matrix=_build_country_matrix(rows))
