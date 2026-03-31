"""CLI entry-point for Red Alert backend.

Usage:
    python -m backend backfill          Download CSV and load into DB
    python -m backend seed-categories   Seed alert_categories table
    python -m backend serve             Run uvicorn dev server
"""

import argparse
import csv
import io
import logging
import sys
import time
from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal, init_db
from backend.ingestion.csv_loader import load_csv_bulk
from backend.ingestion.locations_loader import load_locations
from backend.models.alert import Alert
from backend.models.category import AlertCategory

logger = logging.getLogger(__name__)

CATEGORIES = [
    {"id": 1, "name_he": "ירי רקטות וטילים", "name_en": "Rocket and missile fire"},
    {"id": 2, "name_he": "חדירת כלי טיס עוין", "name_en": "Hostile aircraft intrusion"},
    {"id": 3, "name_he": "רעידת אדמה", "name_en": "Earthquake"},
    {"id": 4, "name_he": "צונאמי", "name_en": "Tsunami"},
    {"id": 5, "name_he": "חדירת מחבלים", "name_en": "Terrorist infiltration"},
    {"id": 6, "name_he": "אירוע חומרים מסוכנים", "name_en": "Hazardous materials event"},
    {"id": 7, "name_he": "אירוע רדיולוגי", "name_en": "Radiological event"},
    {"id": 13, "name_he": "האירוע הסתיים", "name_en": "All clear"},
    {"id": 14, "name_he": "הנחיה מקדימה", "name_en": "Preliminary guidance"},
]


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="red-alert", description="Red Alert CLI")
    sub = parser.add_subparsers(dest="command")

    bf = sub.add_parser("backfill", help="Download CSV and load into database")
    bf.add_argument("--file", help="Load from local CSV file instead of downloading")
    sub.add_parser("seed-categories", help="Seed alert_categories table")

    loc_p = sub.add_parser("load-locations", help="Load locations from cities.json")
    loc_p.add_argument("--file", help="Path to cities.json (defaults to data/cities.json)")

    acled_p = sub.add_parser("acled-sync", help="Sync ACLED conflict events")
    acled_p.add_argument("--from-date", help="Start date (YYYY-MM-DD). Defaults to last sync date.")
    acled_p.add_argument("--to-date", help="End date (YYYY-MM-DD). Defaults to today.")
    acled_p.add_argument("--full", action="store_true", help="Full sync from 2024-01-01, ignoring last sync.")

    acled_csv = sub.add_parser("acled-load", help="Load ACLED events from CSV export file")
    acled_csv.add_argument("--file", required=True, help="Path to ACLED CSV export file")

    serve_p = sub.add_parser("serve", help="Run uvicorn dev server")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--host", default="0.0.0.0")

    return parser


def seed_categories(db: Session) -> int:
    """Insert known alert categories. Skips existing rows."""
    inserted = 0
    for cat_data in CATEGORIES:
        existing = db.query(AlertCategory).filter_by(id=cat_data["id"]).first()
        if not existing:
            db.add(AlertCategory(**cat_data))
            inserted += 1
    db.commit()
    return inserted


def _read_csv_text(csv_path: str | None) -> str:
    """Read CSV text from a local file or download from configured URL."""
    if csv_path:
        logger.info("Reading CSV from local file: %s", csv_path)
        with Path(csv_path).open(encoding="utf-8") as f:
            return f.read()

    url = settings.csv_url
    logger.info("Downloading CSV from %s", url)
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.get(url)
            response.raise_for_status()
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Failed to download CSV: %s", exc)
        sys.exit(1)
    return response.text


def _log_top_locations(db: Session) -> None:
    """Log the top 5 locations by alert count."""
    stmt = (
        select(Alert.location_name, func.count().label("cnt"))
        .group_by(Alert.location_name)
        .order_by(func.count().desc())
        .limit(5)
    )
    rows = db.execute(stmt).all()
    logger.info("Top 5 locations by alert count:")
    for r in rows:
        logger.info("  %s: %d", r.location_name, r.cnt)


def cmd_backfill(csv_path: str | None = None) -> None:
    """Download CSV from configured URL (or read from local file) and load into DB."""
    init_db()
    db = SessionLocal()

    try:
        csv_text = _read_csv_text(csv_path)

        # Count CSV rows
        reader = csv.DictReader(io.StringIO(csv_text))
        row_count = sum(1 for _ in reader)
        logger.info("CSV rows: %d", row_count)

        t0 = time.time()
        inserted = load_csv_bulk(db, csv_text)
        elapsed = time.time() - t0

        logger.info("Inserted %d alert records in %.1f seconds", inserted, elapsed)
        logger.info("CSV rows: %d | Alert records: %d | Time: %.1fs", row_count, inserted, elapsed)

        _log_top_locations(db)
    finally:
        db.close()


def cmd_seed_categories() -> None:
    """Seed the alert categories table."""
    init_db()
    db = SessionLocal()
    try:
        count = seed_categories(db)
        logger.info("Seeded %d categories", count)
    finally:
        db.close()


def cmd_load_locations(cities_path: str | None = None) -> None:
    """Load location metadata from cities.json into the locations table."""
    init_db()
    db = SessionLocal()
    try:
        count = load_locations(db, cities_path)
        logger.info("Loaded %d locations", count)
    finally:
        db.close()


def cmd_acled_sync(
    from_date_str: str | None = None,
    to_date_str: str | None = None,
    full: bool = False,
) -> None:
    """Sync ACLED conflict data to local database."""
    from backend.ingestion.acled_client import get_last_sync_date, ingest_acled_events

    init_db()
    db = SessionLocal()
    try:
        if full:
            event_date_from = "2024-01-01"
        elif from_date_str:
            event_date_from = from_date_str
        else:
            last = get_last_sync_date(db)
            event_date_from = str(last) if last else "2024-01-01"

        event_date_to = to_date_str

        logger.info("ACLED sync: %s to %s", event_date_from, event_date_to or "latest")
        count = ingest_acled_events(db, event_date_from=event_date_from, event_date_to=event_date_to)
        logger.info("ACLED sync complete: %d events inserted", count)
    finally:
        db.close()


def cmd_acled_load(csv_path: str) -> None:
    """Load ACLED events from a CSV export file."""
    from backend.ingestion.acled_csv_loader import load_acled_csv

    init_db()
    db = SessionLocal()
    try:
        count = load_acled_csv(db, csv_path)
        logger.info("ACLED CSV load complete: %d events inserted", count)
    finally:
        db.close()


def cmd_serve(host: str, port: int) -> None:
    """Start the uvicorn development server."""
    import uvicorn

    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "backfill":
        cmd_backfill(csv_path=args.file)
    elif args.command == "seed-categories":
        cmd_seed_categories()
    elif args.command == "load-locations":
        cmd_load_locations(cities_path=args.file)
    elif args.command == "acled-sync":
        cmd_acled_sync(
            from_date_str=args.from_date,
            to_date_str=args.to_date,
            full=args.full,
        )
    elif args.command == "acled-load":
        cmd_acled_load(csv_path=args.file)
    elif args.command == "serve":
        cmd_serve(args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
