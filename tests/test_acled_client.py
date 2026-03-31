"""Tests for ACLED API client: OAuth2 auth, fetch, parse, ingest."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import httpx
import pytest
from backend.ingestion.acled_client import (
    _parse_acled_event,
    fetch_acled_events,
    get_last_sync_date,
    ingest_acled_events,
    update_sync_state,
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models.acled_event import AcledEvent
from backend.models.sync_state import SyncState


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


SAMPLE_ACLED_EVENT: dict = {
    "event_id_cnty": "IRN12345",
    "event_date": "2026-03-01",
    "year": "2026",
    "time_precision": "1",
    "disorder_type": "Political violence",
    "event_type": "Explosions/Remote violence",
    "sub_event_type": "Air/drone strike",
    "actor1": "Military Forces of the United States",
    "assoc_actor_1": "",
    "inter1": "1",
    "actor2": "Military Forces of Iran",
    "assoc_actor_2": "Islamic Revolutionary Guard Corps",
    "inter2": "1",
    "interaction": "11",
    "civilian_targeting": "",
    "iso": "364",
    "region": "Middle East",
    "country": "Iran, Islamic Republic of",
    "admin1": "Isfahan",
    "admin2": "Isfahan",
    "admin3": "",
    "location": "Isfahan",
    "latitude": "32.6539",
    "longitude": "51.6660",
    "geo_precision": "1",
    "source": "Reuters; Al Jazeera",
    "source_scale": "International",
    "notes": "US forces struck military targets near Isfahan.",
    "fatalities": "12",
    "tags": "",
    "timestamp": "1709337600",
}


class TestParseAcledEvent:
    def test_parse_valid_event(self) -> None:
        result = _parse_acled_event(SAMPLE_ACLED_EVENT)
        assert result is not None
        assert result["event_id_cnty"] == "IRN12345"
        assert result["event_date"] == date(2026, 3, 1)
        assert result["year"] == 2026
        assert result["fatalities"] == 12
        assert result["latitude"] == pytest.approx(32.6539)
        assert result["longitude"] == pytest.approx(51.6660)
        assert result["actor1"] == "Military Forces of the United States"
        assert result["actor2"] == "Military Forces of Iran"

    def test_parse_empty_strings_become_none(self) -> None:
        result = _parse_acled_event(SAMPLE_ACLED_EVENT)
        assert result is not None
        assert result["admin3"] is None
        assert result["civilian_targeting"] is None

    def test_parse_missing_event_id_returns_none(self) -> None:
        bad = {**SAMPLE_ACLED_EVENT, "event_id_cnty": ""}
        assert _parse_acled_event(bad) is None

    def test_parse_bad_date_returns_none(self) -> None:
        bad = {**SAMPLE_ACLED_EVENT, "event_date": "not-a-date"}
        assert _parse_acled_event(bad) is None

    def test_parse_missing_lat_returns_none(self) -> None:
        bad = {**SAMPLE_ACLED_EVENT, "latitude": ""}
        assert _parse_acled_event(bad) is None

    def test_parse_fatalities_default_zero(self) -> None:
        data = {**SAMPLE_ACLED_EVENT, "fatalities": ""}
        result = _parse_acled_event(data)
        assert result is not None
        assert result["fatalities"] == 0


class TestFetchAcledEvents:
    @patch("backend.ingestion.acled_client._get_access_token")
    @patch("backend.ingestion.acled_client.httpx.Client")
    def test_fetch_returns_parsed_events(
        self, mock_client_cls: MagicMock, mock_token: MagicMock
    ) -> None:
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [SAMPLE_ACLED_EVENT]}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        events = fetch_acled_events(countries=["Iran, Islamic Republic of"])
        assert len(events) == 1
        assert events[0]["event_id_cnty"] == "IRN12345"

    @patch("backend.ingestion.acled_client._get_access_token")
    @patch("backend.ingestion.acled_client.httpx.Client")
    def test_fetch_empty_response(
        self, mock_client_cls: MagicMock, mock_token: MagicMock
    ) -> None:
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        events = fetch_acled_events()
        assert events == []


class TestIngestAcledEvents:
    @patch("backend.ingestion.acled_client.fetch_acled_events")
    def test_ingest_inserts_events(self, mock_fetch: MagicMock, db: Session) -> None:
        parsed = _parse_acled_event(SAMPLE_ACLED_EVENT)
        assert parsed is not None
        mock_fetch.return_value = [parsed]

        count = ingest_acled_events(db)
        assert count == 1
        assert db.scalar(select(AcledEvent).where(AcledEvent.event_id_cnty == "IRN12345")) is not None

    @patch("backend.ingestion.acled_client.fetch_acled_events")
    def test_ingest_deduplicates(self, mock_fetch: MagicMock, db: Session) -> None:
        parsed = _parse_acled_event(SAMPLE_ACLED_EVENT)
        assert parsed is not None
        mock_fetch.return_value = [parsed]

        count1 = ingest_acled_events(db)
        count2 = ingest_acled_events(db)
        assert count1 == 1
        assert count2 == 0

    @patch("backend.ingestion.acled_client.fetch_acled_events")
    def test_ingest_handles_http_error(self, mock_fetch: MagicMock, db: Session) -> None:
        mock_fetch.side_effect = httpx.ConnectError("Connection refused")

        count = ingest_acled_events(db)
        assert count == 0

    @patch("backend.ingestion.acled_client.fetch_acled_events")
    def test_ingest_skips_invalid_events(self, mock_fetch: MagicMock, db: Session) -> None:
        good = _parse_acled_event(SAMPLE_ACLED_EVENT)
        assert good is not None
        mock_fetch.return_value = [good, None]  # None = failed parse

        count = ingest_acled_events(db)
        assert count == 1


class TestSyncState:
    def test_get_last_sync_date_empty(self, db: Session) -> None:
        assert get_last_sync_date(db) is None

    def test_update_and_get_sync_state(self, db: Session) -> None:
        update_sync_state(db, last_date=date(2026, 3, 15), count=100)
        result = get_last_sync_date(db)
        assert result == date(2026, 3, 15)

    def test_update_sync_state_overwrites(self, db: Session) -> None:
        update_sync_state(db, last_date=date(2026, 3, 1), count=50)
        update_sync_state(db, last_date=date(2026, 3, 15), count=100)
        result = get_last_sync_date(db)
        assert result == date(2026, 3, 15)

        state = db.scalar(select(SyncState).where(SyncState.source == "acled"))
        assert state is not None
        assert state.events_synced == 100
