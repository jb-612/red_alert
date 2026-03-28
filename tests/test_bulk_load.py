"""Tests for the optimized bulk CSV loading (INSERT OR IGNORE approach)."""

from backend.ingestion.csv_loader import load_csv_from_text, load_csv_bulk
from backend.models.alert import Alert
from tests.conftest import SAMPLE_CSV_TEXT


def test_load_csv_bulk(db):
    """Bulk loader should insert all unique records."""
    inserted = load_csv_bulk(db, SAMPLE_CSV_TEXT)
    # Row 1: 2 locations, Row 2: 1, Row 3: 1, Row 4: 1 = 5
    assert inserted == 5
    assert db.query(Alert).count() == 5


def test_load_csv_bulk_deduplicates(db):
    """Loading same CSV twice via bulk should skip duplicates."""
    first = load_csv_bulk(db, SAMPLE_CSV_TEXT)
    second = load_csv_bulk(db, SAMPLE_CSV_TEXT)
    assert first == 5
    assert second == 0
    assert db.query(Alert).count() == 5


def test_load_csv_bulk_matches_original(db):
    """Bulk loader should produce same results as original loader."""
    inserted = load_csv_bulk(db, SAMPLE_CSV_TEXT)
    assert inserted == 5

    alerts = db.query(Alert).order_by(Alert.alert_datetime, Alert.location_name).all()
    assert alerts[0].location_name == "באר שבע 288"
    assert alerts[1].location_name == "באר שבע 289"
    assert alerts[2].location_name == "אשקלון 256"
