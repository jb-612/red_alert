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


# --- Fixtures for new endpoints ---


@pytest.fixture()
def seeded_situation(db_session: Session) -> Session:
    """Seed events spanning two weeks for situation/trend testing.

    Prior week (2026-03-10 to 2026-03-16): 4 events, 8 fatalities
    Current week (2026-03-17 to 2026-03-23): 6 events, 15 fatalities
    Theaters: core_me (7 events), maritime (2 events), global_terror (1 event)
    Countries: Iran (5), Iraq (3), United States (1), Yemen (1)
    """
    base = {
        "year": 2026, "time_precision": 1, "disorder_type": "Political violence",
        "event_type": "Explosions/Remote violence", "sub_event_type": "Air/drone strike",
        "actor1": "Military Forces of the United States", "iso": 364,
        "location": "Isfahan", "latitude": 32.6539, "longitude": 51.6660,
        "theater": "core_me",
    }
    events_data = [
        # Prior week: 4 events, 8 fatalities
        {**base, "event_id_cnty": "S01", "event_date": date(2026, 3, 10),
         "country": "Iran, Islamic Republic of", "fatalities": 3},
        {**base, "event_id_cnty": "S02", "event_date": date(2026, 3, 12),
         "country": "Iraq", "iso": 368, "fatalities": 2,
         "actor1": "Military Forces of Iran", "location": "Basra"},
        {**base, "event_id_cnty": "S03", "event_date": date(2026, 3, 14),
         "country": "Iran, Islamic Republic of", "fatalities": 1, "theater": "maritime",
         "location": "Strait of Hormuz"},
        {**base, "event_id_cnty": "S04", "event_date": date(2026, 3, 16),
         "country": "Iraq", "iso": 368, "fatalities": 2, "location": "Mosul"},
        # Current week: 6 events, 15 fatalities
        {**base, "event_id_cnty": "S05", "event_date": date(2026, 3, 17),
         "country": "Iran, Islamic Republic of", "fatalities": 5},
        {**base, "event_id_cnty": "S06", "event_date": date(2026, 3, 18),
         "country": "Iran, Islamic Republic of", "fatalities": 3},
        {**base, "event_id_cnty": "S07", "event_date": date(2026, 3, 19),
         "country": "Iraq", "iso": 368, "fatalities": 2, "location": "Baghdad"},
        {**base, "event_id_cnty": "S08", "event_date": date(2026, 3, 20),
         "country": "Iran, Islamic Republic of", "fatalities": 1, "theater": "maritime",
         "location": "Bandar Abbas"},
        {**base, "event_id_cnty": "S09", "event_date": date(2026, 3, 21),
         "country": "Yemen", "iso": 887, "fatalities": 4,
         "location": "Sanaa", "actor1": "Ansar Allah"},
        {**base, "event_id_cnty": "S10", "event_date": date(2026, 3, 23),
         "country": "United States", "iso": 840, "fatalities": 0,
         "theater": "global_terror",
         "event_type": "Violence against civilians",
         "actor1": "Unidentified Armed Group (United States)",
         "location": "Dearborn"},
    ]
    for e in events_data:
        db_session.add(AcledEvent(**e))
    db_session.commit()
    yield db_session
    db_session.query(AcledEvent).delete()
    db_session.commit()


class TestSituation:
    """Tests for GET /api/acled/situation."""

    def test_situation_summary(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Full situation response with 10 seeded events."""
        resp = client.get(
            "/api/acled/situation",
            params={"from_date": "2026-03-10", "to_date": "2026-03-23"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # Totals
        assert data["total_events"] == 10
        assert data["total_fatalities"] == 23

        # 7-day trend (last 7 days = 2026-03-17 to 2026-03-23 = 6 events)
        assert data["events_last_7d"] == 6
        assert data["events_prior_7d"] == 4
        assert data["trend_pct"] == pytest.approx(50.0, abs=0.1)

        # Fatalities 7-day
        assert data["fatalities_last_7d"] == 15
        assert data["fatalities_prior_7d"] == 8

        # Counts
        assert data["active_theaters"] == 3  # core_me, maritime, global_terror
        assert data["active_countries"] == 4  # Iran, Iraq, Yemen, US

        # Last event date
        assert data["last_event_date"] == "2026-03-23"

    def test_situation_with_country_filter(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Situation filtered to a single country."""
        resp = client.get(
            "/api/acled/situation",
            params={
                "from_date": "2026-03-10",
                "to_date": "2026-03-23",
                "countries": "Iraq",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 3
        assert data["active_countries"] == 1

    def test_situation_empty(self, client: TestClient) -> None:
        """Situation with no data returns zeroed response."""
        resp = client.get("/api/acled/situation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 0
        assert data["total_fatalities"] == 0
        assert data["events_last_7d"] == 0
        assert data["trend_pct"] is None


class TestTopActors:
    """Tests for GET /api/acled/top-actors."""

    def test_top_actors_default(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Top actors with default limit."""
        resp = client.get(
            "/api/acled/top-actors",
            params={"from_date": "2026-03-10", "to_date": "2026-03-23"},
        )
        assert resp.status_code == 200
        data = resp.json()
        actors = data["actors"]
        assert len(actors) >= 1

        # Top actor should have most events
        top = actors[0]
        assert "actor" in top
        assert "total_events" in top
        assert "total_fatalities" in top
        assert "lethality" in top
        assert "countries" in top
        assert "primary_theater" in top
        assert "events_last_7d" in top
        assert top["total_events"] >= top["events_last_7d"]

    def test_top_actors_limit(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Top actors respects limit parameter."""
        resp = client.get(
            "/api/acled/top-actors",
            params={
                "from_date": "2026-03-10",
                "to_date": "2026-03-23",
                "limit": 2,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["actors"]) <= 2

    def test_top_actors_lethality(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Lethality = fatalities / events."""
        resp = client.get(
            "/api/acled/top-actors",
            params={"from_date": "2026-03-10", "to_date": "2026-03-23"},
        )
        data = resp.json()
        for actor in data["actors"]:
            if actor["total_events"] > 0:
                expected = actor["total_fatalities"] / actor["total_events"]
                assert actor["lethality"] == pytest.approx(expected, abs=0.01)

    def test_top_actors_empty(self, client: TestClient) -> None:
        """Top actors with no data returns empty list."""
        resp = client.get("/api/acled/top-actors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["actors"] == []


class TestCountryMatrix:
    """Tests for GET /api/acled/country-matrix."""

    def test_country_matrix(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Matrix returns country × event-type breakdown."""
        resp = client.get(
            "/api/acled/country-matrix",
            params={"from_date": "2026-03-10", "to_date": "2026-03-23"},
        )
        assert resp.status_code == 200
        data = resp.json()
        matrix = data["matrix"]
        assert len(matrix) >= 1

        # Check structure of each country entry
        for entry in matrix:
            assert "country" in entry
            assert "event_types" in entry
            for et_data in entry["event_types"].values():
                assert "count" in et_data
                assert "fatalities" in et_data

    def test_country_matrix_counts(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Sum of country matrix should equal total events."""
        resp = client.get(
            "/api/acled/country-matrix",
            params={"from_date": "2026-03-10", "to_date": "2026-03-23"},
        )
        data = resp.json()
        total_count = sum(
            et["count"]
            for entry in data["matrix"]
            for et in entry["event_types"].values()
        )
        assert total_count == 10

    def test_country_matrix_with_theater_filter(
        self, client: TestClient, seeded_situation: Session,
    ) -> None:
        """Matrix filtered by theater."""
        resp = client.get(
            "/api/acled/country-matrix",
            params={
                "from_date": "2026-03-10",
                "to_date": "2026-03-23",
                "theaters": "core_me",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # core_me has 7 events across Iran (4) and Iraq (3)
        total_count = sum(
            et["count"]
            for entry in data["matrix"]
            for et in entry["event_types"].values()
        )
        assert total_count == 7

    def test_country_matrix_empty(self, client: TestClient) -> None:
        """Matrix with no data returns empty list."""
        resp = client.get("/api/acled/country-matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert data["matrix"] == []
