"""Tests for ACLED analytics endpoints."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.acled_event import AcledEvent


def _evt(**overrides: object) -> dict:
    defaults: dict = {
        "event_id_cnty": "IRN001",
        "event_date": date(2026, 3, 1),
        "year": 2026,
        "time_precision": 1,
        "disorder_type": "Political violence",
        "event_type": "Explosions/Remote violence",
        "sub_event_type": "Air/drone strike",
        "actor1": "Military Forces of the United States",
        "country": "Iran, Islamic Republic of",
        "iso": 364,
        "location": "Isfahan",
        "latitude": 32.6539,
        "longitude": 51.6660,
        "fatalities": 5,
        "theater": "core_me",
    }
    defaults.update(overrides)
    return defaults


@pytest.fixture()
def seeded_acled(db_session: Session) -> Session:
    """Seed diverse ACLED events for analytics testing."""
    events = [
        # Day 1: 3 events in Iran (spike day)
        _evt(event_id_cnty="A01", event_date=date(2026, 3, 1), fatalities=10),
        _evt(event_id_cnty="A02", event_date=date(2026, 3, 1), fatalities=5,
             sub_event_type="Shelling/artillery/missile attack"),
        _evt(event_id_cnty="A03", event_date=date(2026, 3, 1), fatalities=3,
             event_type="Violence against civilians", civilian_targeting="Civilian targeting",
             actor1="Military Forces of Iran"),
        # Day 2: 1 event in Iraq
        _evt(event_id_cnty="A04", event_date=date(2026, 3, 2), country="Iraq", iso=368,
             location="Al Asad", fatalities=2, actor1="Military Forces of Iran",
             actor2="Military Forces of the United States"),
        # Day 3: 1 maritime event
        _evt(event_id_cnty="A05", event_date=date(2026, 3, 3), location="Strait of Hormuz",
             fatalities=0, theater="maritime", sub_event_type="Attack"),
        # Day 4: 1 global terror event
        _evt(event_id_cnty="A06", event_date=date(2026, 3, 4), country="United States", iso=840,
             location="Dearborn", fatalities=1, theater="global_terror",
             event_type="Violence against civilians", civilian_targeting="Civilian targeting",
             actor1="Unidentified Armed Group (United States)"),
        # Day 5-7: quiet (no events) — for anomaly detection contrast
    ]
    for e in events:
        db_session.add(AcledEvent(**e))
    db_session.commit()
    yield db_session
    db_session.query(AcledEvent).delete()
    db_session.commit()


class TestAcledAnomalies:
    def test_anomalies_endpoint(self, client: TestClient, seeded_acled: Session) -> None:
        resp = client.get("/api/acled/anomalies?threshold=1.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "mean_daily_count" in data
        assert "anomalies" in data
        assert data["total_days_analyzed"] >= 1

    def test_anomalies_empty(self, client: TestClient) -> None:
        resp = client.get("/api/acled/anomalies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_days_analyzed"] >= 0


class TestEscalation:
    def test_escalation_endpoint(self, client: TestClient, seeded_acled: Session) -> None:
        resp = client.get("/api/acled/escalation")
        assert resp.status_code == 200
        data = resp.json()
        assert "theaters" in data

    def test_escalation_empty(self, client: TestClient) -> None:
        resp = client.get("/api/acled/escalation")
        assert resp.status_code == 200


class TestActorProfile:
    def test_actor_profile(self, client: TestClient, seeded_acled: Session) -> None:
        resp = client.get("/api/acled/actor-profile?actor=Military+Forces+of+the+United+States")
        assert resp.status_code == 200
        data = resp.json()
        assert data["actor"] == "Military Forces of the United States"
        assert data["total_events"] >= 1
        assert len(data["countries"]) >= 1

    def test_actor_profile_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/acled/actor-profile?actor=NonexistentActor12345")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 0


class TestTheaterTimeline:
    def test_theater_timeline(self, client: TestClient, seeded_acled: Session) -> None:
        resp = client.get("/api/acled/theater-timeline?granularity=day")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["series"]) >= 1
        assert data["granularity"] == "day"

    def test_theater_timeline_empty(self, client: TestClient) -> None:
        resp = client.get("/api/acled/theater-timeline")
        assert resp.status_code == 200


class TestCivilianImpact:
    def test_civilian_impact(self, client: TestClient, seeded_acled: Session) -> None:
        resp = client.get("/api/acled/civilian-impact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_civilian_events"] >= 1
        assert len(data["by_country"]) >= 1

    def test_civilian_impact_empty(self, client: TestClient) -> None:
        resp = client.get("/api/acled/civilian-impact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_civilian_events"] >= 0
