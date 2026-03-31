from __future__ import annotations

from datetime import date  # noqa: TC003

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.filters import apply_filters
from backend.database import get_db
from backend.db_compat import extract_month, extract_week
from backend.models.alert import Alert
from backend.models.location import Location
from backend.schemas.alert import (
    AlertListResponse,
    AlertResponse,
    CategoryCount,
    GeoPoint,
    LocationCount,
    TimelineBucket,
    TimelineResponse,
)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    """List alerts with optional filtering and pagination."""
    base = select(Alert)
    base = apply_filters(base, from_date, to_date, categories, location, zone=zone)

    total = db.scalar(select(func.count()).select_from(base.subquery()))
    items = db.scalars(
        base.order_by(Alert.alert_datetime.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/timeline", response_model=TimelineResponse)
def alert_timeline(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
) -> TimelineResponse:
    """Alert timeline bucketed by day, week, or month."""
    if granularity == "day":
        period_expr = func.date(Alert.alert_datetime)
    elif granularity == "week":
        period_expr = extract_week(Alert.alert_datetime)
    else:
        period_expr = extract_month(Alert.alert_datetime)

    stmt = select(period_expr.label("period"), func.count().label("count")).group_by("period")
    stmt = apply_filters(stmt, from_date, to_date, categories, location, zone=zone)
    stmt = stmt.order_by("period")

    rows = db.execute(stmt).all()
    return TimelineResponse(
        buckets=[TimelineBucket(period=str(r.period), count=r.count) for r in rows],
        granularity=granularity,
    )


@router.get("/by-category", response_model=list[CategoryCount])
def alerts_by_category(
    from_date: date | None = None,
    to_date: date | None = None,
    location: str | None = Query(None, max_length=200),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> list[CategoryCount]:
    """Alert counts grouped by category."""
    stmt = select(
        Alert.category,
        Alert.category_desc,
        func.count().label("count"),
    ).group_by(Alert.category, Alert.category_desc)
    stmt = apply_filters(stmt, from_date, to_date, categories=None, location=location, zone=zone)
    stmt = stmt.order_by(func.count().desc())

    rows = db.execute(stmt).all()
    return [
        CategoryCount(category=r.category, category_desc=r.category_desc or "", count=r.count)
        for r in rows
    ]


@router.get("/by-location", response_model=list[LocationCount])
def alerts_by_location(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    zone: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> list[LocationCount]:
    """Alert counts grouped by location."""
    stmt = select(
        Alert.location_name,
        func.count().label("count"),
    ).group_by(Alert.location_name)
    stmt = apply_filters(stmt, from_date, to_date, categories, location=None, zone=zone)
    order_func = func.count().desc() if order == "desc" else func.count().asc()
    stmt = stmt.order_by(order_func).limit(limit)

    rows = db.execute(stmt).all()
    return [LocationCount(location_name=r.location_name, count=r.count) for r in rows]


@router.get("/geo", response_model=list[GeoPoint])
def alerts_geo(
    from_date: date | None = None,
    to_date: date | None = None,
    categories: list[int] | None = Query(None),
    zone: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
) -> list[GeoPoint]:
    """Aggregated alert data per location for the map."""
    stmt = (
        select(
            Alert.location_name,
            Location.latitude,
            Location.longitude,
            func.count().label("count"),
            func.group_concat(func.distinct(Alert.category)).label("categories_raw"),
        )
        .join(Location, Alert.location_name == Location.name)
        .where(Location.latitude.isnot(None))
        .group_by(Alert.location_name)
    )

    stmt = apply_filters(stmt, from_date, to_date, categories, location=None, zone=zone)

    rows = db.execute(stmt).all()
    results = []
    for r in rows:
        cat_ids = [int(c) for c in r.categories_raw.split(",") if c] if r.categories_raw else []
        results.append(
            GeoPoint(
                location_name=r.location_name,
                lat=float(r.latitude),
                lng=float(r.longitude),
                count=r.count,
                categories=cat_ids,
            )
        )
    return results
