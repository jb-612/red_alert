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
import time
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal, init_db
from backend.ingestion.csv_loader import load_csv_bulk
from backend.ingestion.locations_loader import load_locations
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
    parser = argparse.ArgumentParser(prog="red-alert", description="Red Alert CLI")
    sub = parser.add_subparsers(dest="command")

    bf = sub.add_parser("backfill", help="Download CSV and load into database")
    bf.add_argument("--file", help="Load from local CSV file instead of downloading")
    sub.add_parser("seed-categories", help="Seed alert_categories table")

    loc_p = sub.add_parser("load-locations", help="Load locations from cities.json")
    loc_p.add_argument("--file", help="Path to cities.json (defaults to data/cities.json)")

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


def cmd_backfill(csv_path: str | None = None) -> None:
    """Download CSV from configured URL (or read from local file) and load into DB."""
    init_db()
    db = SessionLocal()

    try:
        if csv_path:
            logger.info("Reading CSV from local file: %s", csv_path)
            with Path(csv_path).open(encoding="utf-8") as f:
                csv_text = f.read()
        else:
            import httpx

            url = settings.csv_url
            logger.info("Downloading CSV from %s", url)
            with httpx.Client(timeout=120.0) as client:
                response = client.get(url)
                response.raise_for_status()
            csv_text = response.text

        # Count CSV rows
        reader = csv.DictReader(io.StringIO(csv_text))
        row_count = 0
        for _ in reader:
            row_count += 1
        logger.info("CSV rows: %d", row_count)

        t0 = time.time()
        inserted = load_csv_bulk(db, csv_text)
        elapsed = time.time() - t0

        logger.info("Inserted %d alert records in %.1f seconds", inserted, elapsed)
        logger.info("CSV rows: %d | Alert records: %d | Time: %.1fs", row_count, inserted, elapsed)

        # Sample query: top 5 locations
        from sqlalchemy import func, select

        from backend.models.alert import Alert

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

    finally:
        db.close()


def cmd_seed_categories() -> None:
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


def cmd_serve(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "backfill":
        cmd_backfill(csv_path=args.file)
    elif args.command == "seed-categories":
        cmd_seed_categories()
    elif args.command == "load-locations":
        cmd_load_locations(cities_path=args.file)
    elif args.command == "serve":
        cmd_serve(args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
