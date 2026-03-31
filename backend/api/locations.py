from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.alert import Alert
from backend.models.location import Location
from backend.schemas.alert import HierarchyCity, HierarchyZone

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("/search")
def search_locations(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict[str, str | None]]:
    """Search locations by name (Hebrew or English)."""
    stmt = (
        select(Location.name, Location.name_en)
        .where(Location.name.contains(q) | Location.name_en.ilike(f"%{q}%"))
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [{"name": r.name, "name_en": r.name_en} for r in rows]


@router.get("/zones")
def list_zones(db: Session = Depends(get_db)) -> list[dict[str, str | int | None]]:
    """List all distinct zones with city counts."""
    stmt = (
        select(Location.zone, Location.zone_en, func.count().label("city_count"))
        .where(Location.zone.isnot(None), Location.zone != "")
        .group_by(Location.zone, Location.zone_en)
        .order_by(Location.zone_en)
    )
    rows = db.execute(stmt).all()
    return [{"zone": r.zone, "zone_en": r.zone_en, "city_count": r.city_count} for r in rows]


@router.get("/hierarchy", response_model=list[HierarchyZone])
def location_hierarchy(db: Session = Depends(get_db)) -> list[HierarchyZone]:
    """Return location hierarchy grouped by zone for drill-down tree."""
    alert_counts = (
        select(Alert.location_name, func.count().label("cnt"))
        .group_by(Alert.location_name)
        .subquery()
    )

    stmt = (
        select(
            Location.zone,
            Location.zone_en,
            Location.name,
            Location.name_en,
            Location.latitude,
            Location.longitude,
            func.coalesce(alert_counts.c.cnt, 0).label("alert_count"),
        )
        .outerjoin(alert_counts, Location.name == alert_counts.c.location_name)
        .where(Location.zone.isnot(None))
        .where(Location.zone != "")
        .order_by(Location.zone, func.coalesce(alert_counts.c.cnt, 0).desc())
    )

    rows = db.execute(stmt).all()

    zones: dict[str, HierarchyZone] = {}
    for r in rows:
        zone_key = r.zone
        if zone_key not in zones:
            zones[zone_key] = HierarchyZone(
                zone=r.zone,
                zone_en=r.zone_en,
                total_alerts=0,
                cities=[],
            )
        zones[zone_key].total_alerts += r.alert_count
        zones[zone_key].cities.append(
            HierarchyCity(
                name=r.name,
                name_en=r.name_en,
                lat=float(r.latitude) if r.latitude else None,
                lng=float(r.longitude) if r.longitude else None,
                alert_count=r.alert_count,
            )
        )

    return sorted(zones.values(), key=lambda z: z.total_alerts, reverse=True)
