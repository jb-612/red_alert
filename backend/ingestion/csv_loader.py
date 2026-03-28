import csv
import io
import logging
from datetime import datetime

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import settings
from backend.ingestion.deduplication import alert_exists
from backend.models.alert import Alert

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


def parse_csv_row(row: dict) -> list[dict]:
    """Parse a single CSV row into one or more alert dicts.

    The CSV `data` field contains comma-separated locations.
    Each location becomes a separate alert record.
    """
    raw_locations = row.get("data", "")
    locations = [loc.strip() for loc in raw_locations.split(",") if loc.strip()]

    try:
        alert_dt = datetime.fromisoformat(row["alertDate"])
    except (ValueError, KeyError):
        return []

    category = int(row.get("category", 0))
    category_desc = row.get("category_desc", "")
    rid_base = row.get("rid", "")
    matrix_id = int(row["matrix_id"]) if row.get("matrix_id") else None

    results = []
    for i, location in enumerate(locations):
        rid = f"{rid_base}-{i}" if len(locations) > 1 else rid_base
        results.append(
            {
                "alert_datetime": alert_dt,
                "location_name": location,
                "category": category,
                "category_desc": category_desc,
                "rid": rid,
                "matrix_id": matrix_id,
                "source": "csv_backfill",
            }
        )
    return results


def load_csv_from_url(db: Session, url: str | None = None) -> int:
    """Download CSV from URL and load into database."""
    url = url or settings.csv_url
    logger.info("Downloading CSV from %s", url)

    with httpx.Client(timeout=120.0) as client:
        response = client.get(url)
        response.raise_for_status()

    return load_csv_from_text(db, response.text)


def _deduplicate_row(db: Session, row: dict) -> list[Alert]:
    """Parse a CSV row and return only non-duplicate Alert objects."""
    return [
        Alert(**ad)
        for ad in parse_csv_row(row)
        if not alert_exists(db, ad["alert_datetime"], ad["location_name"], ad["category"])
    ]


def load_csv_from_text(db: Session, text: str) -> int:
    """Parse CSV text and load into database with deduplication."""
    reader = csv.DictReader(io.StringIO(text))
    total_inserted = 0
    batch: list[Alert] = []

    for row in reader:
        batch.extend(_deduplicate_row(db, row))
        if len(batch) >= BATCH_SIZE:
            db.add_all(batch)
            db.commit()
            total_inserted += len(batch)
            logger.info("Inserted %d alerts (total: %d)", len(batch), total_inserted)
            batch = []

    if batch:
        db.add_all(batch)
        db.commit()
        total_inserted += len(batch)

    logger.info("CSV load complete. Total inserted: %d", total_inserted)
    return total_inserted


def load_csv_bulk(db: Session, csv_text: str) -> int:
    """Optimized bulk CSV loader using INSERT OR IGNORE.

    The unique index on (alert_datetime, location_name, category) handles
    deduplication at the DB level, avoiding per-row SELECT checks.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    total_inserted = 0
    batch: list[dict] = []

    insert_sql = text(
        "INSERT OR IGNORE INTO alerts "
        "(alert_datetime, location_name, category, category_desc, rid, matrix_id, source) "
        "VALUES (:alert_datetime, :location_name, :category, :category_desc, "
        ":rid, :matrix_id, :source)"
    )

    conn = db.connection()

    for row in reader:
        alert_dicts = parse_csv_row(row)
        batch.extend(alert_dicts)

        if len(batch) >= BATCH_SIZE:
            result = conn.execute(insert_sql, batch)
            total_inserted += result.rowcount
            logger.info("Batch inserted (total so far: %d)", total_inserted)
            batch = []

    if batch:
        result = conn.execute(insert_sql, batch)
        total_inserted += result.rowcount

    db.commit()
    logger.info("Bulk CSV load complete. Total inserted: %d", total_inserted)
    return total_inserted
