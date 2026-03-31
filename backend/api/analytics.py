from __future__ import annotations

import statistics
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, case, cast, distinct, func, select
from sqlalchemy.orm import Session

from backend.api.filters import apply_filters
from backend.database import get_db
from backend.db_compat import extract_dow, extract_hour
from backend.models.alert import Alert
from backend.models.category import AlertCategory
from backend.models.location import Location
from backend.schemas.alert import (
    AnomalyDay,
    AnomalyResponse,
    BestWeekdaysResponse,
    CategoryCount,
    ComparisonDelta,
    ComparisonResponse,
    DateRange,
    HourlyHeatmapCell,
    KpiResponse,
    LocationCount,
    LocationHotHour,
    MostActiveCategory,
    NightScore,
    PeakDay,
    PeriodSummary,
    PrealertCorrelationResponse,
    PrealertLocationStat,
    QuietStreak,
    QuietStreaksResponse,
    RegionAnalytics,
    SleepScoreResponse,
    TimelineBucket,
    TopLocationEntry,
    WeekdayRank,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

PRE_ALERT_CATEGORY = 14
ROCKET_CATEGORY = 1
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 7
MIN_DATES_FOR_STATS = 2


def _empty_kpi() -> KpiResponse:
    return KpiResponse(
        total_alerts=0,
        peak_day=PeakDay(date="", count=0),
        most_active_category=MostActiveCategory(category=0, name="", name_en="", percentage=0.0),
        longest_quiet_days=0,
        date_range=DateRange(**{"from": "", "to": ""}),
        unique_locations=0,
    )


def _get_alert_dates(db: Session, filters: tuple) -> list[date]:
    """Return sorted list of distinct dates that have alerts matching filters."""
    day_expr = func.date(Alert.alert_datetime)
    stmt = select(day_expr.label("day")).group_by("day").order_by("day")
    stmt = apply_filters(stmt, *filters)
    rows = db.execute(stmt).all()
    return [date.fromisoformat(str(r.day)) for r in rows]


def _longest_quiet_days(db: Session, filters: tuple) -> int:
    dates = _get_alert_dates(db, filters)
    if len(dates) < 2:  # noqa: PLR2004
        return 0
    return max((dates[i] - dates[i - 1]).days for i in range(1, len(dates)))


def _lookup_category_name_en(db: Session, category_id: int) -> str:
    """Look up the English name for a category from the alert_categories table."""
    row = db.execute(select(AlertCategory.name_en).where(AlertCategory.id == category_id)).first()
    return row[0] if row else ""


def _query_kpi_parts(db: Session, filters: tuple) -> dict:
    day_expr = func.date(Alert.alert_datetime)

    peak_stmt = (
        select(day_expr.label("day"), func.count().label("cnt"))
        .group_by("day")
        .order_by(func.count().desc())
        .limit(1)
    )
    peak_stmt = apply_filters(peak_stmt, *filters)
    peak_row = db.execute(peak_stmt).first()

    cat_stmt = (
        select(Alert.category, Alert.category_desc, func.count().label("cnt"))
        .group_by(Alert.category, Alert.category_desc)
        .order_by(func.count().desc())
        .limit(1)
    )
    cat_stmt = apply_filters(cat_stmt, *filters)
    cat_row = db.execute(cat_stmt).first()

    range_stmt = select(
        func.min(Alert.alert_datetime).label("earliest"),
        func.max(Alert.alert_datetime).label("latest"),
    )
    range_stmt = apply_filters(range_stmt, *filters)
    range_row = db.execute(range_stmt).first()

    loc_stmt = select(func.count(distinct(Alert.location_name)))
    loc_stmt = apply_filters(loc_stmt, *filters)
    unique_locations = db.scalar(loc_stmt) or 0

    return {
        "peak_row": peak_row,
        "cat_row": cat_row,
        "range_row": range_row,
        "unique_locations": unique_locations,
    }


def _build_kpi(db: Session, filters: tuple, total_alerts: int) -> KpiResponse:
    parts = _query_kpi_parts(db, filters)
    peak_row = parts["peak_row"]
    cat_row = parts["cat_row"]
    range_row = parts["range_row"]

    # name is Hebrew (from category_desc), name_en from alert_categories table
    name_en = _lookup_category_name_en(db, cat_row.category)

    return KpiResponse(
        total_alerts=total_alerts,
        peak_day=PeakDay(date=str(peak_row.day), count=peak_row.cnt),
        most_active_category=MostActiveCategory(
            category=cat_row.category,
            name=cat_row.category_desc or "",
            name_en=name_en,
            percentage=round(cat_row.cnt / total_alerts * 100, 1),
        ),
        longest_quiet_days=_longest_quiet_days(db, filters),
        date_range=DateRange(
            **{
                "from": range_row.earliest.strftime("%Y-%m-%d") if range_row.earliest else "",
                "to": range_row.latest.strftime("%Y-%m-%d") if range_row.latest else "",
            }
        ),
        unique_locations=parts["unique_locations"],
    )


@router.get("/kpi", response_model=KpiResponse)
def kpi(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> KpiResponse:
    """Summary KPI data for the dashboard header."""
    filters = (from_date, to_date, categories, location, zone)

    total_stmt = select(func.count()).select_from(Alert)
    total_stmt = apply_filters(total_stmt, *filters)
    total_alerts = db.scalar(total_stmt) or 0

    if total_alerts == 0:
        return _empty_kpi()

    return _build_kpi(db, filters, total_alerts)


@router.get("/hourly-heatmap", response_model=list[HourlyHeatmapCell])
def hourly_heatmap(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> list[HourlyHeatmapCell]:
    """Hour-of-day x day-of-week heatmap.

    Reveals the "hottest" alert times and best sleep windows.
    Weekday 0=Sunday (Israel week), 6=Saturday.
    """
    stmt = select(
        extract_hour(Alert.alert_datetime).label("hour"),
        extract_dow(Alert.alert_datetime).label("dow_raw"),
        func.count().label("count"),
    ).group_by("hour", "dow_raw")
    stmt = apply_filters(stmt, from_date, to_date, categories, location, zone=zone)

    rows = db.execute(stmt).all()
    results = []
    for r in rows:
        hour = int(r.hour) if r.hour else 0
        # SQLite %w already uses 0=Sunday, matching Israel week convention
        weekday = int(r.dow_raw) if r.dow_raw else 0
        results.append(HourlyHeatmapCell(hour=hour, weekday=weekday, count=r.count))

    return results


def _query_sparklines(
    db: Session,
    location_names: list[str],
    from_date: date | None,
    to_date: date | None,
) -> dict[str, list[dict]]:
    """Get daily alert counts per location for sparkline charts."""
    spark_stmt = (
        select(
            Alert.location_name,
            func.date(Alert.alert_datetime).label("day"),
            func.count().label("count"),
        )
        .where(Alert.location_name.in_(location_names))
        .group_by(Alert.location_name, "day")
    )
    spark_stmt = apply_filters(spark_stmt, from_date, to_date, categories=None, location=None)

    sparklines: dict[str, list[dict]] = {}
    for r in db.execute(spark_stmt).all():
        sparklines.setdefault(r.location_name, []).append({"day": str(r.day), "count": r.count})
    return sparklines


@router.get("/top-locations", response_model=list[TopLocationEntry])
def top_locations(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    zone: str | None = Query(None, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[TopLocationEntry]:
    """Top-N locations with daily sparkline data."""
    filters = (from_date, to_date, categories, None, zone)

    top_stmt = select(
        Alert.location_name,
        func.count().label("total"),
    ).group_by(Alert.location_name)
    top_stmt = apply_filters(top_stmt, *filters)
    top_stmt = top_stmt.order_by(func.count().desc()).limit(limit)
    top_rows = db.execute(top_stmt).all()
    top_names = [r.location_name for r in top_rows]

    if not top_names:
        return []

    sparklines = _query_sparklines(db, top_names, from_date, to_date)

    return [
        TopLocationEntry(
            location_name=r.location_name,
            total=r.total,
            sparkline=sorted(sparklines.get(r.location_name, []), key=lambda x: x["day"]),
        )
        for r in top_rows
    ]


@router.get("/by-region/{zone_en}", response_model=RegionAnalytics)
def analytics_by_region(
    zone_en: str,
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> RegionAnalytics:
    """Analytics filtered to all locations within a specific zone."""
    # Get all location names in this zone
    loc_stmt = select(Location.name).where(Location.zone_en == zone_en)
    location_names = [r[0] for r in db.execute(loc_stmt).all()]

    if not location_names:
        return RegionAnalytics(
            zone_en=zone_en,
            total_alerts=0,
            top_locations=[],
            category_breakdown=[],
            timeline=[],
        )

    # Base filter: alerts in these locations
    base = select(Alert).where(Alert.location_name.in_(location_names))
    filters = (from_date, to_date, categories, None, zone)
    base = apply_filters(base, *filters)
    sub = base.subquery()

    total = db.scalar(select(func.count()).select_from(sub)) or 0

    if total == 0:
        return RegionAnalytics(
            zone_en=zone_en,
            total_alerts=0,
            top_locations=[],
            category_breakdown=[],
            timeline=[],
        )

    # Top locations
    top_stmt = (
        select(Alert.location_name, func.count().label("count"))
        .where(Alert.location_name.in_(location_names))
        .group_by(Alert.location_name)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_stmt = apply_filters(top_stmt, *filters)
    top_rows = db.execute(top_stmt).all()

    # Category breakdown
    cat_stmt = (
        select(Alert.category, Alert.category_desc, func.count().label("count"))
        .where(Alert.location_name.in_(location_names))
        .group_by(Alert.category, Alert.category_desc)
        .order_by(func.count().desc())
    )
    cat_stmt = apply_filters(cat_stmt, *filters)
    cat_rows = db.execute(cat_stmt).all()

    # Timeline (daily)  # noqa: ERA001
    day_expr = func.date(Alert.alert_datetime)
    tl_stmt = (
        select(day_expr.label("period"), func.count().label("count"))
        .where(Alert.location_name.in_(location_names))
        .group_by("period")
        .order_by("period")
    )
    tl_stmt = apply_filters(tl_stmt, *filters)
    tl_rows = db.execute(tl_stmt).all()

    return RegionAnalytics(
        zone_en=zone_en,
        total_alerts=total,
        top_locations=[
            LocationCount(location_name=r.location_name, count=r.count) for r in top_rows
        ],
        category_breakdown=[
            CategoryCount(category=r.category, category_desc=r.category_desc or "", count=r.count)
            for r in cat_rows
        ],
        timeline=[TimelineBucket(period=str(r.period), count=r.count) for r in tl_rows],
    )


# ---------------------------------------------------------------------------
# Phase 4: Lifestyle Analytics
# ---------------------------------------------------------------------------


def _query_disturbed_nights(db: Session, filters: tuple) -> set[date]:
    """Return set of night-start dates that had alerts in the 22:00-06:59 window."""
    hour_expr = cast(extract_hour(Alert.alert_datetime), Integer)
    night_date_expr = case(
        (hour_expr >= NIGHT_START_HOUR, func.date(Alert.alert_datetime)),
        else_=func.date(Alert.alert_datetime, "-1 day"),
    )

    stmt = (
        select(night_date_expr.label("night_date"))
        .where((hour_expr >= NIGHT_START_HOUR) | (hour_expr < NIGHT_END_HOUR))
        .group_by("night_date")
    )
    stmt = apply_filters(stmt, *filters)

    rows = db.execute(stmt).all()
    return {date.fromisoformat(str(r.night_date)) for r in rows}


def _build_night_range(
    from_date: date | None,
    to_date: date | None,
    db: Session,
    filters: tuple,
) -> list[date]:
    """Return list of night-start dates in the range.

    A night starting on date D covers 22:00 D to 06:59 D+1.
    For from_date=Jan 10 to_date=Jan 12, nights are [Jan 10, Jan 11].
    """
    if not from_date or not to_date:
        range_stmt = select(
            func.min(Alert.alert_datetime).label("earliest"),
            func.max(Alert.alert_datetime).label("latest"),
        )
        range_stmt = apply_filters(range_stmt, *filters)
        row = db.execute(range_stmt).first()
        if not row or not row.earliest:
            return []
        from_date = from_date or row.earliest.date()
        to_date = to_date or row.latest.date()

    nights: list[date] = []
    current = from_date
    while current < to_date:
        nights.append(current)
        current += timedelta(days=1)
    return nights


@router.get("/sleep-score", response_model=SleepScoreResponse)
def sleep_score(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> SleepScoreResponse:
    """Sleep quality score based on alert-free nights (22:00-06:59)."""
    filters = (from_date, to_date, categories, location, zone)
    nights = _build_night_range(from_date, to_date, db, filters)

    if not nights:
        return SleepScoreResponse(score=100.0, total_nights=0, peaceful_nights=0, trend=[])

    disturbed = _query_disturbed_nights(db, filters)
    trend = [NightScore(date=n.isoformat(), peaceful=(n not in disturbed)) for n in nights]
    peaceful_count = sum(1 for n in nights if n not in disturbed)
    score = round(peaceful_count / len(nights) * 100, 1)

    return SleepScoreResponse(
        score=score,
        total_nights=len(nights),
        peaceful_nights=peaceful_count,
        trend=trend,
    )


_WEEKDAY_NAMES = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def _query_weekday_counts(db: Session, filters: tuple) -> dict[int, int]:
    """Return {weekday: alert_count} for all 7 days (0=Sunday)."""
    dow_expr = cast(extract_dow(Alert.alert_datetime), Integer)
    stmt = select(dow_expr.label("dow"), func.count().label("cnt")).group_by("dow")
    stmt = apply_filters(stmt, *filters)
    rows = db.execute(stmt).all()
    counts = dict.fromkeys(range(7), 0)
    for r in rows:
        counts[r.dow] = r.cnt
    return counts


def _query_hot_hours(db: Session, filters: tuple, top_n: int) -> list[LocationHotHour]:
    """Return peak alert hour for each of the top N locations."""
    top_stmt = (
        select(Alert.location_name, func.count().label("total"))
        .group_by(Alert.location_name)
        .order_by(func.count().desc())
        .limit(top_n)
    )
    top_stmt = apply_filters(top_stmt, *filters)
    top_names = [r.location_name for r in db.execute(top_stmt).all()]

    if not top_names:
        return []

    hour_expr = cast(extract_hour(Alert.alert_datetime), Integer)
    hour_stmt = (
        select(
            Alert.location_name,
            hour_expr.label("hour"),
            func.count().label("cnt"),
        )
        .where(Alert.location_name.in_(top_names))
        .group_by(Alert.location_name, "hour")
    )
    hour_stmt = apply_filters(hour_stmt, *filters)
    rows = db.execute(hour_stmt).all()

    best: dict[str, tuple[int, int]] = {}
    for r in rows:
        prev = best.get(r.location_name)
        if prev is None or r.cnt > prev[1]:
            best[r.location_name] = (r.hour, r.cnt)

    return [
        LocationHotHour(location_name=name, peak_hour=best[name][0], alert_count=best[name][1])
        for name in top_names
        if name in best
    ]


@router.get("/best-weekdays", response_model=BestWeekdaysResponse)
def best_weekdays(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    top_locations: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> BestWeekdaysResponse:
    """Rank weekdays by fewest alerts and show peak hours per top location."""
    filters = (from_date, to_date, categories, location, zone)
    counts = _query_weekday_counts(db, filters)

    sorted_days = sorted(counts.items(), key=lambda x: x[1])
    weekdays = [
        WeekdayRank(
            weekday=dow,
            weekday_name=_WEEKDAY_NAMES[dow],
            alert_count=cnt,
            rank=rank,
        )
        for rank, (dow, cnt) in enumerate(sorted_days, 1)
    ]

    hot_hours = _query_hot_hours(db, filters, top_locations)

    return BestWeekdaysResponse(weekdays=weekdays, hot_hours=hot_hours)


def _compute_inner_streaks(
    alert_dates: list[date],
) -> list[tuple[date, date, int]]:
    """Compute quiet streaks between consecutive alert dates.

    Returns list of (start, end, days) where start/end are first/last quiet days.
    Only includes streaks of length >= 1.
    """
    streaks: list[tuple[date, date, int]] = []
    for i in range(1, len(alert_dates)):
        gap_days = (alert_dates[i] - alert_dates[i - 1]).days - 1
        if gap_days >= 1:
            start = alert_dates[i - 1] + timedelta(days=1)
            end = alert_dates[i] - timedelta(days=1)
            streaks.append((start, end, gap_days))
    return streaks


def _empty_streaks_response(from_date: date | None, end_date: date) -> QuietStreaksResponse:
    """Build a streaks response when no alerts exist in the range."""
    if not from_date:
        return QuietStreaksResponse(current_streak=None, longest_streak=None, top_streaks=[])
    total_days = (end_date - from_date).days + 1
    streak = QuietStreak(
        start_date=from_date.isoformat(),
        end_date=end_date.isoformat(),
        days=total_days,
    )
    return QuietStreaksResponse(current_streak=streak, longest_streak=streak, top_streaks=[streak])


def _collect_edge_streaks(
    alert_dates: list[date],
    from_date: date | None,
    end_date: date,
    streaks: list[tuple[date, date, int]],
) -> QuietStreak | None:
    """Append leading/trailing streaks and return the current streak if any."""
    start_date = from_date or alert_dates[0]
    leading_days = (alert_dates[0] - start_date).days
    if leading_days >= 1:
        streaks.append((start_date, alert_dates[0] - timedelta(days=1), leading_days))

    trailing_days = (end_date - alert_dates[-1]).days
    if trailing_days >= 1:
        trail_start = alert_dates[-1] + timedelta(days=1)
        streaks.append((trail_start, end_date, trailing_days))
        return QuietStreak(
            start_date=trail_start.isoformat(),
            end_date=end_date.isoformat(),
            days=trailing_days,
        )
    return None


def _build_quiet_streaks(
    db: Session,
    filters: tuple,
    from_date: date | None,
    to_date: date | None,
    top_n: int,
) -> QuietStreaksResponse:
    """Build the full quiet streaks response."""
    alert_dates = _get_alert_dates(db, filters)
    end_date = to_date or datetime.now(tz=UTC).date()

    if not alert_dates:
        return _empty_streaks_response(from_date, end_date)

    streaks = _compute_inner_streaks(alert_dates)
    current_streak = _collect_edge_streaks(alert_dates, from_date, end_date, streaks)

    streaks.sort(key=lambda s: s[2], reverse=True)
    top = streaks[:top_n]

    longest = None
    if top:
        s = top[0]
        longest = QuietStreak(start_date=s[0].isoformat(), end_date=s[1].isoformat(), days=s[2])

    top_streaks = [
        QuietStreak(start_date=s[0].isoformat(), end_date=s[1].isoformat(), days=s[2]) for s in top
    ]

    return QuietStreaksResponse(
        current_streak=current_streak,
        longest_streak=longest,
        top_streaks=top_streaks,
    )


@router.get("/quiet-streaks", response_model=QuietStreaksResponse)
def quiet_streaks(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    top_n: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> QuietStreaksResponse:
    """Find consecutive alert-free day stretches."""
    filters = (from_date, to_date, categories, location, zone)
    return _build_quiet_streaks(db, filters, from_date, to_date, top_n)


# ---------------------------------------------------------------------------
# Phase 5: Comparison + Prediction
# ---------------------------------------------------------------------------


def _query_daily_counts(db: Session, filters: tuple) -> list[tuple[str, int]]:
    """Return (date_str, count) pairs for each day with alerts."""
    day_expr = func.date(Alert.alert_datetime)
    stmt = select(day_expr.label("day"), func.count().label("cnt")).group_by("day").order_by("day")
    stmt = apply_filters(stmt, *filters)
    rows = db.execute(stmt).all()
    return [(str(r.day), r.cnt) for r in rows]


def _compute_anomalies(
    daily_counts: list[tuple[str, int]],
    threshold: float,
    limit: int,
) -> AnomalyResponse:
    """Compute z-score anomalies from daily count data (pure function)."""
    if len(daily_counts) < MIN_DATES_FOR_STATS:
        return AnomalyResponse(
            mean_daily_count=0.0,
            std_daily_count=0.0,
            threshold=threshold,
            total_days_analyzed=len(daily_counts),
            anomalies=[],
        )

    counts = [c for _, c in daily_counts]
    mu = statistics.mean(counts)
    sigma = statistics.stdev(counts)

    if sigma == 0:
        return AnomalyResponse(
            mean_daily_count=round(mu, 2),
            std_daily_count=0.0,
            threshold=threshold,
            total_days_analyzed=len(daily_counts),
            anomalies=[],
        )

    anomalies = _find_anomaly_days(daily_counts, mu, sigma, threshold)
    anomalies.sort(key=lambda a: abs(a.z_score), reverse=True)

    return AnomalyResponse(
        mean_daily_count=round(mu, 2),
        std_daily_count=round(sigma, 2),
        threshold=threshold,
        total_days_analyzed=len(daily_counts),
        anomalies=anomalies[:limit],
    )


def _find_anomaly_days(
    daily_counts: list[tuple[str, int]],
    mu: float,
    sigma: float,
    threshold: float,
) -> list[AnomalyDay]:
    """Filter daily counts to those exceeding z-score threshold."""
    result: list[AnomalyDay] = []
    for day, count in daily_counts:
        z = (count - mu) / sigma
        if abs(z) > threshold:
            result.append(
                AnomalyDay(
                    date=day,
                    count=count,
                    z_score=round(z, 2),
                    direction="high" if z > 0 else "low",
                )
            )
    return result


@router.get("/anomalies", response_model=AnomalyResponse)
def anomalies(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    threshold: float = Query(2.0, ge=1.0, le=4.0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AnomalyResponse:
    """Detect anomalous days using z-score on daily alert counts."""
    filters = (from_date, to_date, categories, location, zone)
    daily = _query_daily_counts(db, filters)
    return _compute_anomalies(daily, threshold, limit)


def _build_period_summary(
    db: Session,
    from_date: date,
    to_date: date,
    categories: list[int] | None,
    location: str | None,
    zone: str | None = None,
) -> PeriodSummary:
    """Build a summary of alerts for a single date range."""
    filters = (from_date, to_date, categories, location, zone)

    total = db.scalar(apply_filters(select(func.count()).select_from(Alert), *filters)) or 0

    unique_locs = (
        db.scalar(apply_filters(select(func.count(distinct(Alert.location_name))), *filters)) or 0
    )

    cat_stmt = (
        select(Alert.category, Alert.category_desc, func.count().label("count"))
        .group_by(Alert.category, Alert.category_desc)
        .order_by(func.count().desc())
    )
    cat_rows = db.execute(apply_filters(cat_stmt, *filters)).all()

    loc_stmt = (
        select(Alert.location_name, func.count().label("count"))
        .group_by(Alert.location_name)
        .order_by(func.count().desc())
        .limit(10)
    )
    loc_rows = db.execute(apply_filters(loc_stmt, *filters)).all()

    tl_rows = db.execute(
        apply_filters(
            select(
                func.date(Alert.alert_datetime).label("period"),
                func.count().label("count"),
            )
            .group_by("period")
            .order_by("period"),
            *filters,
        )
    ).all()

    return PeriodSummary(
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        total_alerts=total,
        unique_locations=unique_locs,
        top_categories=[
            CategoryCount(
                category=r.category,
                category_desc=r.category_desc or "",
                count=r.count,
            )
            for r in cat_rows
        ],
        top_locations=[
            LocationCount(location_name=r.location_name, count=r.count) for r in loc_rows
        ],
        timeline=[TimelineBucket(period=str(r.period), count=r.count) for r in tl_rows],
    )


def _compute_delta(a: PeriodSummary, b: PeriodSummary) -> ComparisonDelta:
    """Compute change from period A to period B."""
    pct = None
    if a.total_alerts > 0:
        pct = round((b.total_alerts - a.total_alerts) / a.total_alerts * 100, 1)
    return ComparisonDelta(
        total_alerts_delta=b.total_alerts - a.total_alerts,
        total_alerts_pct=pct,
        unique_locations_delta=b.unique_locations - a.unique_locations,
    )


@router.get("/compare", response_model=ComparisonResponse)
def compare(
    period_a_from: date = Query(...),
    period_a_to: date = Query(...),
    period_b_from: date = Query(...),
    period_b_to: date = Query(...),
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> ComparisonResponse:
    """Compare metrics between two date ranges."""
    a = _build_period_summary(db, period_a_from, period_a_to, categories, location, zone)
    b = _build_period_summary(db, period_b_from, period_b_to, categories, location, zone)
    return ComparisonResponse(period_a=a, period_b=b, delta=_compute_delta(a, b))


def _query_prealert_totals(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    location: str | None,
    zone: str | None = None,
) -> dict[str, int]:
    """Count category 14 alerts per location."""
    stmt = (
        select(Alert.location_name, func.count().label("cnt"))
        .where(Alert.category == PRE_ALERT_CATEGORY)
        .group_by(Alert.location_name)
    )
    stmt = apply_filters(stmt, from_date, to_date, categories=None, location=location, zone=zone)
    return {r.location_name: r.cnt for r in db.execute(stmt).all()}


def _query_prealert_followed(
    db: Session,
    from_date: date | None,
    to_date: date | None,
    location: str | None,
    window_minutes: int,
    zone: str | None = None,
) -> dict[str, int]:
    """Count cat 14 alerts followed by cat 1 at same location within window."""
    a = Alert.__table__.alias("a")
    b = Alert.__table__.alias("b")
    window_jd = window_minutes / 1440.0

    exists_subq = (
        select(func.count())
        .select_from(b)
        .where(b.c.location_name == a.c.location_name)
        .where(b.c.category == ROCKET_CATEGORY)
        .where(func.julianday(b.c.alert_datetime) - func.julianday(a.c.alert_datetime) > 0)
        .where(func.julianday(b.c.alert_datetime) - func.julianday(a.c.alert_datetime) <= window_jd)
        .correlate(a)
        .scalar_subquery()
    )

    stmt = (
        select(a.c.location_name, func.count().label("cnt"))
        .where(a.c.category == PRE_ALERT_CATEGORY)
        .where(exists_subq > 0)
        .group_by(a.c.location_name)
    )

    if from_date:
        stmt = stmt.where(a.c.alert_datetime >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(a.c.alert_datetime <= datetime.combine(to_date, datetime.max.time()))
    if location:
        stmt = stmt.where(a.c.location_name.contains(location))
    if zone:
        zone_names = select(Location.name).where(Location.zone_en == zone)
        stmt = stmt.where(a.c.location_name.in_(zone_names))

    return {r.location_name: r.cnt for r in db.execute(stmt).all()}


def _build_correlation_response(
    totals: dict[str, int],
    followed: dict[str, int],
    window_minutes: int,
    min_prealerts: int,
    limit: int,
) -> PrealertCorrelationResponse:
    """Assemble the correlation response from totals and followed dicts."""
    overall_total = sum(totals.values())
    overall_followed = sum(followed.values())

    locations = []
    for loc_name, total in totals.items():
        if total < min_prealerts:
            continue
        fol = followed.get(loc_name, 0)
        locations.append(
            PrealertLocationStat(
                location_name=loc_name,
                total_prealerts=total,
                followed_by_actual=fol,
                probability=round(fol / total, 4) if total > 0 else 0.0,
            )
        )

    locations.sort(key=lambda x: x.probability, reverse=True)

    return PrealertCorrelationResponse(
        window_minutes=window_minutes,
        overall_total_prealerts=overall_total,
        overall_followed=overall_followed,
        overall_probability=(
            round(overall_followed / overall_total, 4) if overall_total > 0 else 0.0
        ),
        locations=locations[:limit],
    )


@router.get("/prealert-correlation", response_model=PrealertCorrelationResponse)
def prealert_correlation(
    from_date: date | None = None,
    to_date: date | None = None,
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    window_minutes: int = Query(30, ge=1, le=60),
    min_prealerts: int = Query(5, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PrealertCorrelationResponse:
    """Pre-alert (cat 14) to actual alert (cat 1) correlation by location."""
    totals = _query_prealert_totals(db, from_date, to_date, location, zone)
    followed = _query_prealert_followed(db, from_date, to_date, location, window_minutes, zone)
    return _build_correlation_response(totals, followed, window_minutes, min_prealerts, limit)
