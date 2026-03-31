"""Tests for ACLED API endpoints."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.acled_event import AcledEvent


def _make_event(**overrides: object) -> dict:
    defaults: dict = {
        "event_id_cnty": "IRN001",
        "event_date": date(2026, 3, 1),
        "year": 2026,
        "time_precision": 1,
        "disorder_type": "Political violence",
        "event_type": "Explosions/Remote violence",
        "sub_event_type": "Air/drone strike",
        "actor1": "Military Forces of the United States",
        "actor2": "Military Forces of Iran",
        "country": "Iran, Islamic Republic of",
        "iso": 364,
        "location": "Isfahan",
        "latitude": 32.6539,
        "longitude": 51.6660,
        "fatalities": 5,
    }
    defaults.update(overrides)
    return defaults


@pytest.fixture()
def seeded_db(db_session: Session) -> Session:
    """Seed ACLED events into the shared test database."""
    db_session.add(AcledEvent(**_make_event(event_id_cnty="IRN001", fatalities=5)))
    db_session.add(AcledEvent(**_make_event(
        event_id_cnty="IRN002",
        event_date=date(2026, 3, 2),
        sub_event_type="Shelling/artillery/missile attack",
        fatalities=10,
    )))
    db_session.add(AcledEvent(**_make_event(
        event_id_cnty="IRQ001",
        country="Iraq",
        iso=368,
        location="Al Asad",
        event_date=date(2026, 3, 3),
        actor1="Military Forces of Iran",
        actor2="Military Forces of the United States",
        fatalities=2,
    )))
    db_session.commit()
    yield db_session
    # Cleanup
    db_session.query(AcledEvent).delete()
    db_session.commit()


class TestListEndpoint:
    def test_empty_db(self, client: TestClient) -> None:
        resp = client.get("/api/acled")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    def test_returns_events(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    def test_country_filter(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled?countries=Iraq")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_date_filter(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled?from_date=2026-03-02&to_date=2026-03-02")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_pagination(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2


class TestGeoEndpoint:
    def test_geo_returns_points(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled/geo")
        assert resp.status_code == 200
        points = resp.json()
        assert len(points) >= 2


class TestTimelineEndpoint:
    def test_timeline_day(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled/timeline?granularity=day")
        assert resp.status_code == 200
        data = resp.json()
        assert data["granularity"] == "day"
        assert len(data["buckets"]) >= 1

    def test_timeline_empty(self, client: TestClient) -> None:
        resp = client.get("/api/acled/timeline")
        assert resp.status_code == 200


class TestByCountryEndpoint:
    def test_by_country(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled/by-country")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestByTypeEndpoint:
    def test_by_type(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled/by-type")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestByActorEndpoint:
    def test_by_actor(self, client: TestClient, seeded_db: Session) -> None:
        resp = client.get("/api/acled/by-actor")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestSyncStatusEndpoint:
    def test_sync_status(self, client: TestClient) -> None:
        resp = client.get("/api/acled/sync-status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_events" in data
