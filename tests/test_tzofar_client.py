from unittest.mock import patch

import httpx

from backend.ingestion.tzofar_client import (
    _parse_response,
    ingest_tzofar_alerts,
)
from backend.ingestion.utils import strip_bom


def test_strip_bom_removes_bom():
    bom_text = "\ufeffhello"
    assert strip_bom(bom_text) == "hello"


def test_strip_bom_no_bom_unchanged():
    text = "hello"
    assert strip_bom(text) == "hello"


def test_strip_bom_empty_string():
    assert strip_bom("") == ""


def test_parse_response_extracts_alerts():
    json_text = """[
        {
            "date": "2024-01-15T10:30:00",
            "name": "\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1 - \u05de\u05e8\u05db\u05d6",
            "category": 1,
            "title": "\u05d9\u05e8\u05d9 \u05e8\u05e7\u05d8\u05d5\u05ea \u05d5\u05d8\u05d9\u05dc\u05d9\u05dd"
        }
    ]"""
    alerts = _parse_response(json_text)
    assert len(alerts) == 1
    assert alerts[0]["location_name"] == "\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1 - \u05de\u05e8\u05db\u05d6"
    assert alerts[0]["category"] == 1
    assert alerts[0]["source"] == "tzofar"


def test_parse_response_skips_invalid_dates():
    json_text = """[
        {
            "date": "not-a-date",
            "name": "test",
            "category": 1
        }
    ]"""
    alerts = _parse_response(json_text)
    assert len(alerts) == 0


def test_parse_response_handles_empty_list():
    alerts = _parse_response("[]")
    assert alerts == []


def test_parse_response_preserves_hebrew():
    json_text = """[
        {
            "date": "2024-01-15T10:30:00",
            "name": "\u05d9\u05e8\u05d5\u05e9\u05dc\u05d9\u05dd",
            "category": 1,
            "title": "\u05d9\u05e8\u05d9 \u05e8\u05e7\u05d8\u05d5\u05ea \u05d5\u05d8\u05d9\u05dc\u05d9\u05dd"
        }
    ]"""
    alerts = _parse_response(json_text)
    assert alerts[0]["location_name"] == "\u05d9\u05e8\u05d5\u05e9\u05dc\u05d9\u05dd"


# --- WI-2.1: HTTP error handling tests ---


def test_ingest_handles_http_error(db: "Session") -> None:  # noqa: F821
    """ingest_tzofar_alerts returns 0 when HTTP status error occurs."""
    mock_response = httpx.Response(status_code=500, request=httpx.Request("GET", "http://test"))
    with patch(
        "backend.ingestion.tzofar_client.fetch_tzofar_alerts",
        side_effect=httpx.HTTPStatusError(
            "Server error", request=httpx.Request("GET", "http://test"), response=mock_response
        ),
    ):
        result = ingest_tzofar_alerts(db)
    assert result == 0


def test_ingest_handles_connect_error(db: "Session") -> None:  # noqa: F821
    """ingest_tzofar_alerts returns 0 when connection fails."""
    with patch(
        "backend.ingestion.tzofar_client.fetch_tzofar_alerts",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        result = ingest_tzofar_alerts(db)
    assert result == 0


def test_ingest_handles_timeout(db: "Session") -> None:  # noqa: F821
    """ingest_tzofar_alerts returns 0 when request times out."""
    with patch(
        "backend.ingestion.tzofar_client.fetch_tzofar_alerts",
        side_effect=httpx.TimeoutException("Request timed out"),
    ):
        result = ingest_tzofar_alerts(db)
    assert result == 0
