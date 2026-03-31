"""Load ACLED conflict events from a CSV export file."""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path

from sqlalchemy import Connection, text
from sqlalchemy.orm import Session

from backend.ingestion.acled_client import _parse_acled_event
from backend.ingestion.utils import strip_bom

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000

_INSERT_SQL = text(
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


def load_acled_csv(db: Session, csv_path: str) -> int:
    """Load ACLED events from a CSV export file into the database.

    Args:
        db: SQLAlchemy session.
        csv_path: Path to the ACLED CSV export file.

    Returns:
        Number of new events inserted.
    """
    csv_text = Path(csv_path).read_text(encoding="utf-8")
    csv_text = strip_bom(csv_text)

    reader = csv.DictReader(io.StringIO(csv_text))
    conn = db.connection()
    total_inserted = 0
    batch: list[dict] = []

    for row in reader:
        parsed = _parse_acled_event(row)
        if parsed is None:
            continue
        batch.append(parsed)
        if len(batch) >= BATCH_SIZE:
            total_inserted += _flush_batch(conn, batch)
            batch = []

    if batch:
        total_inserted += _flush_batch(conn, batch)

    db.commit()
    logger.info("ACLED CSV load complete: %d events inserted from %s", total_inserted, csv_path)
    return total_inserted


def _flush_batch(conn: Connection, batch: list[dict]) -> int:
    """Execute batch insert and return rowcount."""
    result = conn.execute(_INSERT_SQL, batch)
    return int(result.rowcount)
