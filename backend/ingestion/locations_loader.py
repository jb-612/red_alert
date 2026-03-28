"""Load location metadata from cities.json into the locations table."""

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.models.location import Location

logger = logging.getLogger(__name__)

DEFAULT_CITIES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cities.json"


def _is_valid_city(city: dict) -> bool:
    """Check if a city entry has a usable name and coordinates."""
    name = city.get("name", "").strip()
    if not name or name == "בחר הכל":
        return False
    lat: float = city.get("lat", 0)
    lng: float = city.get("lng", 0)
    return lat != 0 or lng != 0


def _update_existing(existing: Location, city: dict) -> None:
    """Update an existing location record with new city data."""
    updatable_fields = ["name_en", "name_ru", "name_ar", "zone", "zone_en"]
    for field in updatable_fields:
        value = city.get(field)
        if value:
            setattr(existing, field, value)
    existing.latitude = city.get("lat", 0)
    existing.longitude = city.get("lng", 0)
    countdown = city.get("countdown")
    if countdown:
        existing.countdown_sec = countdown


def _upsert_city(db: Session, city: dict) -> None:
    """Insert or update a single city location."""
    name = city.get("name", "").strip()
    existing = db.query(Location).filter_by(name=name).first()
    if existing:
        _update_existing(existing, city)
    else:
        db.add(
            Location(
                name=name,
                name_en=city.get("name_en"),
                name_ru=city.get("name_ru"),
                name_ar=city.get("name_ar"),
                zone=city.get("zone"),
                zone_en=city.get("zone_en"),
                latitude=city.get("lat", 0),
                longitude=city.get("lng", 0),
                countdown_sec=city.get("countdown"),
            )
        )


def load_locations(db: Session, cities_path: str | Path | None = None) -> int:
    """Parse cities.json and upsert into the locations table.

    Returns the number of locations loaded.
    """
    path = Path(cities_path) if cities_path else DEFAULT_CITIES_PATH
    with path.open(encoding="utf-8") as f:
        cities = json.load(f)

    valid_cities = [c for c in cities if _is_valid_city(c)]
    for city in valid_cities:
        _upsert_city(db, city)

    db.commit()
    logger.info("Loaded %d locations into the database", len(valid_cities))
    return len(valid_cities)
