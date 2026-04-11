"""ACLED aggregate ingestion — fetches pre-computed Explorer overview JSON files.

ACLED's "Explorer" platform publishes static JSON overview files served without
authentication from a CDN. These are the only source of recent (≤12 months)
aggregated conflict data available to the Research tier.

File layout:
    {time}_{disorder}_overview.json

- time ∈ {week, month, year}:
    - "week"  → daily buckets, past ~7 days
    - "month" → daily buckets, past ~29 days
    - "year"  → monthly buckets, past 12 months
- disorder ∈ {all, demonstrations, politicalviolence, insurgency, atrocities,
             repression, terroristactivity, foreignmilitary}

Each file contains: timeline (global), types (global totals), eventTypes
(global breakdown), countryTimeline (long-format per-country per-bucket),
countries (per-country totals), and latestUpdate.

We ingest the countryTimeline rows into acled_aggregates. Global totals and
event-type breakdowns can be derived by summation at query time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Final

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.ingestion.acled_constants import (
    COUNTRY_THEATER_MAP,
    THEATER_EXTENDED_ME,
    THEATER_GLOBAL_TERROR,
)

logger = logging.getLogger(__name__)

AGGREGATE_BASE_URL: Final[str] = (
    "https://apps.acleddata.com/newexplorer/standard//data/acled/"
)

TIME_VARIANTS: Final[tuple[str, ...]] = ("week", "month", "year")

DISORDER_VARIANTS: Final[tuple[str, ...]] = (
    "all",
    "demonstrations",
    "politicalviolence",
    "insurgency",
    "atrocities",
    "repression",
    "terroristactivity",
    "foreignmilitary",
)

TIME_TO_GRANULARITY: Final[dict[str, str]] = {
    "week": "day",
    "month": "day",
    "year": "month",
}

THEATER_OTHER: Final[str] = "other"

# Aggregate files use short country names; event ingestion uses ISO-style long names.
# Map short → long so COUNTRY_THEATER_MAP lookups succeed for Middle East countries.
_AGGREGATE_COUNTRY_ALIAS: Final[dict[str, str]] = {
    "Iran": "Iran, Islamic Republic of",
    "Syria": "Syrian Arab Republic",
}

# Aliases for countries the Middle-East-focused COUNTRY_THEATER_MAP doesn't list
# but which belong to recognized theaters.
_ADDITIONAL_THEATER_MAP: Final[dict[str, str]] = {
    "Egypt": THEATER_EXTENDED_ME,
    "Libya": THEATER_EXTENDED_ME,
    "Sudan": THEATER_EXTENDED_ME,
    "Canada": THEATER_GLOBAL_TERROR,
    "Australia": THEATER_GLOBAL_TERROR,
}


@dataclass(frozen=True)
class AggregateRow:
    """One normalized row ready for insertion into acled_aggregates."""

    bucket_start_date: date
    granularity: str
    country_id: int
    country_name: str
    disorder_type: str
    events: int
    fatalities: int
    exposure: int
    exposure_pct: float
    theater: str
    latest_update: date
    source_file: str


def aggregate_url(time_variant: str, disorder: str) -> str:
    """Construct the full URL of an Explorer overview file."""
    return f"{AGGREGATE_BASE_URL}{time_variant}_{disorder}_overview.json"


def classify_country_theater(country_name: str) -> str:
    """Classify an aggregate-file country name into a conflict theater."""
    canonical = _AGGREGATE_COUNTRY_ALIAS.get(country_name, country_name)
    if canonical in COUNTRY_THEATER_MAP:
        return COUNTRY_THEATER_MAP[canonical]
    if country_name in _ADDITIONAL_THEATER_MAP:
        return _ADDITIONAL_THEATER_MAP[country_name]
    return THEATER_OTHER


def fetch_overview(time_variant: str, disorder: str) -> dict:
    """Fetch an overview file from the ACLED CDN as parsed JSON."""
    url = aggregate_url(time_variant, disorder)
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers={"User-Agent": "red-alert-ingest/1.0"})
        resp.raise_for_status()
        payload: dict = resp.json()
        return payload


def _safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _build_id_name_map(countries: list[dict]) -> dict[int, str]:
    return {int(c["id"]): str(c["name"]) for c in countries if "id" in c and "name" in c}


def _parse_row(
    raw: dict,
    id_to_name: dict[int, str],
    disorder: str,
    granularity: str,
    latest_update: date,
    source_file: str,
) -> AggregateRow | None:
    """Convert a single countryTimeline row into a typed AggregateRow."""
    bucket_date = _safe_date(raw.get("date"))
    if bucket_date is None:
        return None
    try:
        country_id = int(raw["id"])
    except (KeyError, ValueError, TypeError):
        return None

    country_name = id_to_name.get(country_id, f"id-{country_id}")
    return AggregateRow(
        bucket_start_date=bucket_date,
        granularity=granularity,
        country_id=country_id,
        country_name=country_name,
        disorder_type=disorder,
        events=int(raw.get("events") or 0),
        fatalities=int(raw.get("fatalities") or 0),
        exposure=int(raw.get("exposure") or 0),
        exposure_pct=float(raw.get("exposure_pct") or 0),
        theater=classify_country_theater(country_name),
        latest_update=latest_update,
        source_file=source_file,
    )


def parse_overview(
    payload: dict,
    time_variant: str,
    disorder: str,
) -> list[AggregateRow]:
    """Flatten an overview JSON payload into storage-ready AggregateRow objects."""
    country_timeline = payload.get("countryTimeline") or []
    countries_list = payload.get("countries") or []
    id_to_name = _build_id_name_map(countries_list)

    latest_update = _safe_date(payload.get("latestUpdate")) or datetime.now(tz=UTC).date()
    granularity = TIME_TO_GRANULARITY[time_variant]
    source_file = f"{time_variant}_{disorder}_overview.json"

    rows: list[AggregateRow] = []
    for raw in country_timeline:
        parsed = _parse_row(raw, id_to_name, disorder, granularity, latest_update, source_file)
        if parsed is not None:
            rows.append(parsed)
    return rows


_UPSERT_SQL = text(
    "INSERT OR REPLACE INTO acled_aggregates "
    "(bucket_start_date, granularity, country_id, country_name, disorder_type, "
    "events, fatalities, exposure, exposure_pct, theater, latest_update, "
    "source_file, ingested_at) "
    "VALUES (:bucket_start_date, :granularity, :country_id, :country_name, "
    ":disorder_type, :events, :fatalities, :exposure, :exposure_pct, :theater, "
    ":latest_update, :source_file, :ingested_at)"
)


def _row_to_params(row: AggregateRow, now: datetime) -> dict:
    return {
        "bucket_start_date": row.bucket_start_date,
        "granularity": row.granularity,
        "country_id": row.country_id,
        "country_name": row.country_name,
        "disorder_type": row.disorder_type,
        "events": row.events,
        "fatalities": row.fatalities,
        "exposure": row.exposure,
        "exposure_pct": row.exposure_pct,
        "theater": row.theater,
        "latest_update": row.latest_update,
        "source_file": row.source_file,
        "ingested_at": now,
    }


def upsert_aggregates(db: Session, rows: list[AggregateRow]) -> int:
    """Insert-or-replace aggregate rows. Idempotent on the unique key."""
    if not rows:
        return 0
    now = datetime.now(tz=UTC)
    params = [_row_to_params(r, now) for r in rows]
    db.connection().execute(_UPSERT_SQL, params)
    db.commit()
    return len(rows)


def sync_overview(db: Session, time_variant: str, disorder: str) -> int:
    """Fetch one overview file, parse it, and upsert into the DB."""
    payload = fetch_overview(time_variant, disorder)
    rows = parse_overview(payload, time_variant, disorder)
    return upsert_aggregates(db, rows)


def sync_all_aggregates(db: Session) -> int:
    """Sync every combination of (time, disorder). Skips individual failures."""
    total = 0
    for time_variant in TIME_VARIANTS:
        for disorder in DISORDER_VARIANTS:
            total += _safe_sync_one(db, time_variant, disorder)
    return total


def _safe_sync_one(db: Session, time_variant: str, disorder: str) -> int:
    try:
        return sync_overview(db, time_variant, disorder)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("ACLED aggregate sync failed for %s/%s: %s", time_variant, disorder, exc)
        return 0
