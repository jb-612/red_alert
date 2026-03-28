from datetime import datetime

from backend.ingestion.csv_loader import load_csv_bulk, load_csv_from_text, parse_csv_row
from backend.models.alert import Alert
from tests.conftest import SAMPLE_CSV_TEXT


def test_parse_csv_row_single_location():
    row = {
        "data": "אשקלון 256",
        "date": "24.07.2014",
        "time": "17:05:35",
        "alertDate": "2014-07-24T17:06:00",
        "category": "1",
        "category_desc": "ירי רקטות וטילים",
        "matrix_id": "1",
        "rid": "2",
    }
    results = parse_csv_row(row)
    assert len(results) == 1
    assert results[0]["location_name"] == "אשקלון 256"
    assert results[0]["category"] == 1
    assert results[0]["alert_datetime"] == datetime(2014, 7, 24, 17, 6)
    assert results[0]["rid"] == "2"


def test_parse_csv_row_multiple_locations():
    row = {
        "data": "באר שבע 288, באר שבע 289, באר שבע 291",
        "date": "24.07.2014",
        "time": "17:05:26",
        "alertDate": "2014-07-24T17:05:00",
        "category": "1",
        "category_desc": "ירי רקטות וטילים",
        "matrix_id": "1",
        "rid": "1",
    }
    results = parse_csv_row(row)
    assert len(results) == 3
    assert results[0]["location_name"] == "באר שבע 288"
    assert results[1]["location_name"] == "באר שבע 289"
    assert results[2]["location_name"] == "באר שבע 291"
    assert results[0]["rid"] == "1-0"
    assert results[1]["rid"] == "1-1"


def test_parse_csv_row_preserves_hebrew():
    row = {
        "data": "ירושלים",
        "alertDate": "2024-01-01T00:00:00",
        "category": "1",
        "category_desc": "ירי רקטות וטילים",
        "matrix_id": "1",
        "rid": "99",
    }
    results = parse_csv_row(row)
    assert results[0]["location_name"] == "ירושלים"


def test_parse_csv_row_invalid_date_returns_empty():
    row = {
        "data": "תל אביב",
        "alertDate": "invalid",
        "category": "1",
    }
    results = parse_csv_row(row)
    assert results == []


def test_load_csv_from_text(db):
    inserted = load_csv_from_text(db, SAMPLE_CSV_TEXT)
    # Row 1: 2 locations, Row 2: 1 location, Row 3: 1 location, Row 4: 1 location = 5 total
    assert inserted == 5
    assert db.query(Alert).count() == 5


def test_load_csv_from_text_deduplicates(db):
    """Loading same CSV twice should not create duplicates."""
    first_load = load_csv_from_text(db, SAMPLE_CSV_TEXT)
    second_load = load_csv_from_text(db, SAMPLE_CSV_TEXT)
    assert first_load == 5
    assert second_load == 0
    assert db.query(Alert).count() == 5


def test_load_csv_from_text_strips_bom(db):
    """CSV text with UTF-8 BOM prefix should still parse correctly."""
    bom_csv = "\ufeff" + SAMPLE_CSV_TEXT
    inserted = load_csv_from_text(db, bom_csv)
    assert inserted == 5


def test_load_csv_bulk_strips_bom(db):
    """Bulk loader handles UTF-8 BOM prefix."""
    bom_csv = "\ufeff" + SAMPLE_CSV_TEXT
    inserted = load_csv_bulk(db, bom_csv)
    assert inserted == 5
