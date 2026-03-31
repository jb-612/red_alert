"""ACLED conflict data ingestion client with OAuth2 authentication."""

from __future__ import annotations

import logging
import time
from datetime import UTC, date, datetime

import httpx
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.config import settings
from backend.ingestion.acled_constants import (
    ACLED_CONFLICT_EVENT_TYPES,
    ACLED_TARGET_COUNTRIES,
    COUNTRY_THEATER_MAP,
    MARITIME_KEYWORDS,
    THEATER_CORE_ME,
    THEATER_MARITIME,
)
from backend.models.sync_state import SyncState

logger = logging.getLogger(__name__)

ACLED_PAGE_SIZE = 5000


def classify_theater(country: str, location: str, notes: str | None) -> str:
    """Classify an event into a conflict theater based on country and context."""
    text_to_check = f"{location} {notes or ''}".lower()
    if any(kw in text_to_check for kw in MARITIME_KEYWORDS):
        return THEATER_MARITIME
    return COUNTRY_THEATER_MAP.get(country, THEATER_CORE_ME)

# Module-level token cache
_token_cache_token: str = ""
_token_cache_expires_at: float = 0.0


def _get_access_token() -> str:
    """Obtain or reuse a cached ACLED OAuth2 Bearer token."""
    global _token_cache_token, _token_cache_expires_at  # noqa: PLW0603
    now = time.time()
    if _token_cache_token and now < _token_cache_expires_at:
        return _token_cache_token

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            settings.acled_token_url,
            data={
                "username": settings.acled_username,
                "password": settings.acled_password,
                "grant_type": "password",
                "client_id": settings.acled_client_id,
            },
        )
        resp.raise_for_status()

    body = resp.json()
    _token_cache_token = body["access_token"]
    _token_cache_expires_at = now + body.get("expires_in", 86400) - 300
    return _token_cache_token


def _build_acled_params(
    countries: list[str] | None,
    event_date_from: str | None,
    event_date_to: str | None,
    event_types: list[str] | None,
    limit: int,
    offset: int,
) -> dict[str, str]:
    """Build query parameters for ACLED API request."""
    params: dict[str, str] = {"limit": str(limit)}
    if offset > 0:
        params["offset"] = str(offset)
    if countries:
        params["country"] = "|".join(countries)
    if event_types:
        params["event_type"] = "|".join(event_types)
    if event_date_from and event_date_to:
        params["event_date"] = f"{event_date_from}|{event_date_to}"
        params["event_date_where"] = "BETWEEN"
    elif event_date_from:
        params["event_date"] = event_date_from
        params["event_date_where"] = ">="
    return params


def fetch_acled_events(
    countries: list[str] | None = None,
    event_date_from: str | None = None,
    event_date_to: str | None = None,
    event_types: list[str] | None = None,
    limit: int = ACLED_PAGE_SIZE,
) -> list[dict]:
    """Fetch conflict events from ACLED API with pagination."""
    token = _get_access_token()
    all_events: list[dict] = []
    offset = 0

    with httpx.Client(timeout=60.0) as client:
        while True:
            params = _build_acled_params(
                countries, event_date_from, event_date_to, event_types, limit, offset
            )
            resp = client.get(
                settings.acled_api_url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            parsed = [_parse_acled_event(e) for e in data]
            all_events.extend([e for e in parsed if e is not None])
            if len(data) < limit:
                break
            offset += limit

    return all_events


def _extract_core_fields(raw: dict) -> tuple[str, date, float, float] | None:
    """Extract and validate required fields: event_id, date, lat, lng."""
    event_id = raw.get("event_id_cnty", "").strip()
    if not event_id:
        return None
    try:
        event_date_val = date.fromisoformat(raw["event_date"])
    except (ValueError, KeyError):
        return None
    try:
        lat = float(raw["latitude"])
        lng = float(raw["longitude"])
    except (ValueError, KeyError, TypeError):
        return None
    return event_id, event_date_val, lat, lng


def _safe_int(val: str | int | None) -> int | None:
    """Convert a value to int, returning None on failure."""
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _nullable(val: str | None) -> str | None:
    """Return None for empty strings, otherwise the value."""
    return val or None


def _parse_acled_event(raw: dict) -> dict | None:
    """Normalize a single ACLED API event dict for database insertion."""
    core = _extract_core_fields(raw)
    if core is None:
        return None
    event_id, event_date_val, lat, lng = core
    return _build_event_dict(raw, event_id, event_date_val, lat, lng)


def _build_event_dict(
    raw: dict, event_id: str, event_date_val: date, lat: float, lng: float
) -> dict:
    """Assemble the full event dict from validated core fields and raw data."""
    return {
        "event_id_cnty": event_id,
        "event_date": event_date_val,
        "year": int(raw.get("year", event_date_val.year)),
        "time_precision": int(raw.get("time_precision", 0)),
        "disorder_type": raw.get("disorder_type", ""),
        "event_type": raw.get("event_type", ""),
        "sub_event_type": raw.get("sub_event_type", ""),
        "actor1": raw.get("actor1", ""),
        "assoc_actor_1": _nullable(raw.get("assoc_actor_1")),
        "inter1": _safe_int(raw.get("inter1")),
        "actor2": _nullable(raw.get("actor2")),
        "assoc_actor_2": _nullable(raw.get("assoc_actor_2")),
        "inter2": _safe_int(raw.get("inter2")),
        "interaction": _safe_int(raw.get("interaction")),
        "civilian_targeting": _nullable(raw.get("civilian_targeting")),
        "country": raw.get("country", ""),
        "iso": int(raw.get("iso", 0)),
        "region": _nullable(raw.get("region")),
        "admin1": _nullable(raw.get("admin1")),
        "admin2": _nullable(raw.get("admin2")),
        "admin3": _nullable(raw.get("admin3")),
        "location": raw.get("location", ""),
        "latitude": lat,
        "longitude": lng,
        "geo_precision": _safe_int(raw.get("geo_precision")),
        "source": _nullable(raw.get("source")),
        "source_scale": _nullable(raw.get("source_scale")),
        "notes": _nullable(raw.get("notes")),
        "fatalities": int(raw.get("fatalities") or 0),
        "tags": _nullable(raw.get("tags")),
        "timestamp": _safe_int(raw.get("timestamp")),
        "theater": classify_theater(
            raw.get("country", ""),
            raw.get("location", ""),
            raw.get("notes"),
        ),
    }


def ingest_acled_events(
    db: Session,
    countries: list[str] | None = None,
    event_date_from: str | None = None,
    event_date_to: str | None = None,
) -> int:
    """Fetch ACLED events and insert using INSERT OR IGNORE deduplication."""
    countries = countries or ACLED_TARGET_COUNTRIES
    event_types = ACLED_CONFLICT_EVENT_TYPES

    try:
        events = fetch_acled_events(
            countries=countries,
            event_date_from=event_date_from,
            event_date_to=event_date_to,
            event_types=event_types,
        )
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.warning("ACLED API request failed: %s", exc)
        return 0

    valid = [e for e in events if e is not None]
    if not valid:
        return 0

    return _bulk_insert_events(db, valid)


def _bulk_insert_events(db: Session, events: list[dict]) -> int:
    """Bulk insert events using INSERT OR IGNORE and update sync state."""
    insert_sql = text(
        "INSERT OR IGNORE INTO acled_events "
        "(event_id_cnty, event_date, year, time_precision, disorder_type, "
        "event_type, sub_event_type, actor1, assoc_actor_1, inter1, "
        "actor2, assoc_actor_2, inter2, interaction, civilian_targeting, "
        "country, iso, region, admin1, admin2, admin3, location, "
        "latitude, longitude, geo_precision, source, source_scale, "
        "notes, fatalities, tags, timestamp, theater) "
        "VALUES (:event_id_cnty, :event_date, :year, :time_precision, :disorder_type, "
        ":event_type, :sub_event_type, :actor1, :assoc_actor_1, :inter1, "
        ":actor2, :assoc_actor_2, :inter2, :interaction, :civilian_targeting, "
        ":country, :iso, :region, :admin1, :admin2, :admin3, :location, "
        ":latitude, :longitude, :geo_precision, :source, :source_scale, "
        ":notes, :fatalities, :tags, :timestamp, :theater)"
    )

    conn = db.connection()
    total_inserted = 0
    batch_size = 500

    for i in range(0, len(events), batch_size):
        batch = events[i : i + batch_size]
        result = conn.execute(insert_sql, batch)
        total_inserted += result.rowcount

    db.commit()
    logger.info("ACLED ingest complete. Inserted %d of %d events", total_inserted, len(events))

    max_date = max(e["event_date"] for e in events)
    update_sync_state(db, last_date=max_date, count=total_inserted)

    return total_inserted


def get_last_sync_date(db: Session) -> date | None:
    """Get the last successfully synced event date for ACLED."""
    row = db.execute(
        select(SyncState.last_sync_date).where(SyncState.source == "acled")
    ).first()
    return row[0] if row else None


def update_sync_state(db: Session, last_date: date, count: int) -> None:
    """Update or create sync state record for ACLED."""
    existing = db.scalar(select(SyncState).where(SyncState.source == "acled"))
    if existing:
        existing.last_sync_date = last_date
        existing.last_sync_at = datetime.now(tz=UTC)
        existing.events_synced = count
    else:
        db.add(
            SyncState(
                source="acled",
                last_sync_date=last_date,
                last_sync_at=datetime.now(tz=UTC),
                events_synced=count,
            )
        )
    db.commit()
