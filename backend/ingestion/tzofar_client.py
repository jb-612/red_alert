import json
import logging
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from backend.config import settings
from backend.ingestion.deduplication import alert_exists
from backend.ingestion.utils import strip_bom
from backend.models.alert import Alert

logger = logging.getLogger(__name__)


def fetch_tzofar_alerts(url: str | None = None) -> list[dict]:
    """Fetch alert history from Tzofar API."""
    url = url or settings.tzofar_api_url
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()

    text = strip_bom(response.text)
    return _parse_response(text)


def _parse_response(text: str) -> list[dict]:
    """Parse JSON response into list of alert dicts."""

    data = json.loads(text)
    if not isinstance(data, list):
        data = data.get("alerts", []) if isinstance(data, dict) else []

    alerts = []
    for item in data:
        try:
            alert_dt = datetime.fromisoformat(str(item.get("date", "")))
        except (ValueError, TypeError):
            continue

        alerts.append(
            {
                "alert_datetime": alert_dt,
                "location_name": item.get("name", item.get("data", "")),
                "category": int(item.get("category", 0)),
                "category_desc": item.get("category_desc", item.get("title", "")),
                "source": "tzofar",
            }
        )
    return alerts


def ingest_tzofar_alerts(db: Session, url: str | None = None) -> int:
    """Fetch from Tzofar API and insert deduped alerts into database."""
    try:
        raw_alerts = fetch_tzofar_alerts(url)
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.warning("Tzofar API request failed: %s", exc)
        return 0
    inserted = 0

    for alert_data in raw_alerts:
        if not alert_exists(
            db,
            alert_data["alert_datetime"],
            alert_data["location_name"],
            alert_data["category"],
        ):
            db.add(Alert(**alert_data))
            inserted += 1

    db.commit()
    logger.info("Tzofar ingest complete. Inserted %d of %d alerts", inserted, len(raw_alerts))
    return inserted
