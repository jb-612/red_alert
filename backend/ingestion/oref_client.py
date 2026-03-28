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


def _build_oref_headers() -> dict[str, str]:
    """Build required headers for OREF API requests."""
    return {
        "Referer": settings.oref_referer,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": settings.oref_user_agent,
    }


def _parse_oref_response(text: str) -> list[dict]:
    """Parse OREF JSON response into list of alert dicts."""
    data = json.loads(text)
    if not isinstance(data, list):
        data = data.get("alerts", []) if isinstance(data, dict) else []

    alerts: list[dict] = []
    for item in data:
        try:
            alert_dt = datetime.fromisoformat(str(item.get("alertDate", "")))
        except (ValueError, TypeError):
            continue

        alerts.append(
            {
                "alert_datetime": alert_dt,
                "location_name": item.get("data", ""),
                "category": int(item.get("category", 0)),
                "category_desc": item.get("category_desc", ""),
                "source": "oref",
            }
        )
    return alerts


def fetch_oref_history(url: str | None = None) -> list[dict]:
    """Fetch alert history from OREF API with required headers and BOM stripping."""
    url = url or settings.oref_history_url
    headers = _build_oref_headers()

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()

    text = strip_bom(response.text)
    return _parse_oref_response(text)


def ingest_oref_history(db: Session, url: str | None = None) -> int:
    """Fetch from OREF API and insert deduped alerts. Returns 0 on failure."""
    try:
        raw_alerts = fetch_oref_history(url)
    except httpx.HTTPStatusError:
        logger.warning("OREF API returned HTTP error (possibly geo-blocked)")
        return 0
    except httpx.ConnectError:
        logger.warning("OREF API connection failed (possibly geo-blocked)")
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
    logger.info("OREF ingest complete. Inserted %d of %d alerts", inserted, len(raw_alerts))
    return inserted
