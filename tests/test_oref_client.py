from unittest.mock import MagicMock, patch

import httpx
from backend.ingestion.oref_client import (
    _parse_oref_response,
    fetch_oref_history,
    ingest_oref_history,
)
from sqlalchemy.orm import Session

from backend.models.alert import Alert

SAMPLE_OREF_JSON = """[
    {
        "data": "תל אביב - מרכז העיר",
        "date": "2024-01-15T10:30:00",
        "time": "10:30",
        "alertDate": "2024-01-15T10:30:00",
        "category": 1,
        "category_desc": "ירי רקטות וטילים",
        "matrix_id": 4,
        "rid": "12345"
    },
    {
        "data": "חיפה - כרמל",
        "date": "2024-01-15T10:31:00",
        "time": "10:31",
        "alertDate": "2024-01-15T10:31:00",
        "category": 1,
        "category_desc": "ירי רקטות וטילים",
        "matrix_id": 4,
        "rid": "12346"
    }
]"""

BOM_OREF_JSON = "\ufeff" + SAMPLE_OREF_JSON


def test_parse_oref_response_basic() -> None:
    alerts = _parse_oref_response(SAMPLE_OREF_JSON)
    assert len(alerts) == 2
    assert alerts[0]["location_name"] == "תל אביב - מרכז העיר"
    assert alerts[0]["category"] == 1
    assert alerts[0]["source"] == "oref"
    assert alerts[1]["location_name"] == "חיפה - כרמל"


def test_parse_oref_response_skips_invalid_dates() -> None:
    json_text = """[
        {
            "data": "תל אביב",
            "alertDate": "not-a-date",
            "category": 1,
            "category_desc": "test"
        },
        {
            "data": "חיפה",
            "alertDate": "2024-01-15T10:30:00",
            "category": 1,
            "category_desc": "test"
        }
    ]"""
    alerts = _parse_oref_response(json_text)
    assert len(alerts) == 1
    assert alerts[0]["location_name"] == "חיפה"


def test_parse_oref_response_preserves_hebrew() -> None:
    json_text = """[
        {
            "data": "ירושלים",
            "alertDate": "2024-01-15T10:30:00",
            "category": 1,
            "category_desc": "ירי רקטות וטילים"
        }
    ]"""
    alerts = _parse_oref_response(json_text)
    assert alerts[0]["location_name"] == "ירושלים"
    assert alerts[0]["category_desc"] == "ירי רקטות וטילים"


def test_fetch_sends_required_headers() -> None:
    mock_response = MagicMock()
    mock_response.text = SAMPLE_OREF_JSON
    mock_response.raise_for_status = MagicMock()

    with patch("backend.ingestion.oref_client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        fetch_oref_history("https://example.com/test")

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        headers = call_args[1].get("headers", call_args.kwargs.get("headers", {}))
        assert headers["Referer"] == "https://www.oref.org.il/"
        assert headers["X-Requested-With"] == "XMLHttpRequest"
        assert "Mozilla" in headers["User-Agent"]


def test_ingest_handles_geo_block(db: Session) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Forbidden", request=MagicMock(), response=mock_response
    )

    with patch("backend.ingestion.oref_client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = ingest_oref_history(db)

    assert result == 0
    assert db.query(Alert).count() == 0


def test_ingest_handles_connect_error(db: Session) -> None:
    with patch("backend.ingestion.oref_client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_cls.return_value = mock_client

        result = ingest_oref_history(db)

    assert result == 0
    assert db.query(Alert).count() == 0


def test_ingest_deduplicates(db: Session) -> None:
    mock_response = MagicMock()
    mock_response.text = SAMPLE_OREF_JSON
    mock_response.raise_for_status = MagicMock()

    with patch("backend.ingestion.oref_client.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        first = ingest_oref_history(db)
        second = ingest_oref_history(db)

    assert first == 2
    assert second == 0
    assert db.query(Alert).count() == 2
