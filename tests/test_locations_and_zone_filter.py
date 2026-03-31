"""Tests for location search, zones endpoint, zone filter, and by-location ordering."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from backend.api.filters import apply_filters
from backend.models.alert import Alert
from backend.models.category import AlertCategory
from backend.models.location import Location

SAMPLE_CITIES = [
    {
        "name": "תל אביב",
        "name_en": "Tel Aviv",
        "zone": "דן",
        "zone_en": "Dan",
        "lat": 32.0853,
        "lng": 34.7818,
        "countdown": 90,
    },
    {
        "name": "חולון",
        "name_en": "Holon",
        "zone": "דן",
        "zone_en": "Dan",
        "lat": 32.0114,
        "lng": 34.7748,
        "countdown": 90,
    },
    {
        "name": "באר שבע",
        "name_en": "Be'er Sheva",
        "zone": "נגב",
        "zone_en": "Negev",
        "lat": 31.2518,
        "lng": 34.7913,
        "countdown": 60,
    },
    {
        "name": "אשדוד",
        "name_en": "Ashdod",
        "zone": "לכיש",
        "zone_en": "Lakhish",
        "lat": 31.8040,
        "lng": 34.6553,
        "countdown": 45,
    },
]


@pytest.fixture(autouse=True)
def seed_data(db_session):
    """Insert sample locations and alerts before each test, clean up after."""
    for city in SAMPLE_CITIES:
        db_session.add(
            Location(
                name=city["name"],
                name_en=city["name_en"],
                zone=city["zone"],
                zone_en=city["zone_en"],
                latitude=city["lat"],
                longitude=city["lng"],
                countdown_sec=city["countdown"],
            )
        )

    alerts = [
        Alert(
            alert_datetime=datetime(2023, 10, 7, 6, 30, tzinfo=UTC),
            location_name="תל אביב",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2023, 10, 7, 6, 31, tzinfo=UTC),
            location_name="חולון",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2023, 10, 7, 7, 0, tzinfo=UTC),
            location_name="תל אביב",
            category=2,
            category_desc="חדירת כלי טיס עוין",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            location_name="באר שבע",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 1, 16, 11, 0, tzinfo=UTC),
            location_name="אשדוד",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
    ]
    db_session.add_all(alerts)
    db_session.commit()
    yield
    db_session.query(Alert).delete()
    db_session.query(Location).delete()
    db_session.query(AlertCategory).delete()
    db_session.commit()


# ---- GET /api/locations/search Tests ----


def test_search_locations_hebrew(client):
    """Search returns results for Hebrew text."""
    response = client.get("/api/locations/search?q=תל")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names = {r["name"] for r in data}
    assert "תל אביב" in names


def test_search_locations_english(client):
    """Search returns results for English text (case insensitive)."""
    response = client.get("/api/locations/search?q=tel")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    names_en = {r["name_en"] for r in data}
    assert "Tel Aviv" in names_en


def test_search_locations_respects_limit(client):
    """Search respects the limit parameter."""
    response = client.get("/api/locations/search?q=ו&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1


def test_search_locations_no_match(client):
    """Search returns empty list for non-matching query."""
    response = client.get("/api/locations/search?q=zzzznotfound")
    assert response.status_code == 200
    data = response.json()
    assert data == []


# ---- GET /api/locations/zones Tests ----


def test_list_zones(client):
    """Returns non-empty list of zones with city counts."""
    response = client.get("/api/locations/zones")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Each zone has expected fields
    for zone in data:
        assert "zone" in zone
        assert "zone_en" in zone
        assert "city_count" in zone
        assert zone["city_count"] >= 1


def test_list_zones_dan_count(client):
    """Dan zone should have 2 cities (Tel Aviv, Holon)."""
    response = client.get("/api/locations/zones")
    data = response.json()
    dan = next((z for z in data if z["zone_en"] == "Dan"), None)
    assert dan is not None
    assert dan["city_count"] == 2


# ---- by-location order param Tests ----


def test_by_location_order_desc(client):
    """Default desc order returns most-alerted first."""
    response = client.get("/api/alerts/by-location")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # First result should have >= count of second
    assert data[0]["count"] >= data[1]["count"]


def test_by_location_order_asc(client):
    """order=asc returns least-alerted first."""
    response = client.get("/api/alerts/by-location?order=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # First result should have <= count of second
    assert data[0]["count"] <= data[1]["count"]


# ---- apply_filters zone filter Tests ----


def test_apply_filters_zone_reduces_results(db_session):
    """Zone filter reduces results to only alerts in that zone's locations."""
    stmt = select(func.count()).select_from(Alert)
    # No zone filter: all 5 alerts
    stmt_all = apply_filters(
        stmt,
        from_date=None,
        to_date=None,
        categories=None,
        location=None,
        zone=None,
    )
    count_all = db_session.scalar(stmt_all)
    assert count_all == 5

    # With Dan zone filter: only Tel Aviv (2) + Holon (1) = 3
    stmt_dan = select(func.count()).select_from(Alert)
    stmt_dan = apply_filters(
        stmt_dan,
        from_date=None,
        to_date=None,
        categories=None,
        location=None,
        zone="Dan",
    )
    count_dan = db_session.scalar(stmt_dan)
    assert count_dan == 3


def test_apply_filters_zone_negev(db_session):
    """Zone filter for Negev returns only Be'er Sheva alerts."""
    stmt = select(Alert)
    stmt = apply_filters(
        stmt,
        from_date=None,
        to_date=None,
        categories=None,
        location=None,
        zone="Negev",
    )
    results = db_session.scalars(stmt).all()
    assert len(results) == 1
    assert results[0].location_name == "באר שבע"


def test_apply_filters_zone_nonexistent(db_session):
    """Zone filter for a non-existent zone returns no results."""
    stmt = select(func.count()).select_from(Alert)
    stmt = apply_filters(
        stmt,
        from_date=None,
        to_date=None,
        categories=None,
        location=None,
        zone="Nonexistent",
    )
    count = db_session.scalar(stmt)
    assert count == 0


# ---- Zone filter through API endpoints ----


def test_alerts_list_zone_filter(client):
    """Zone filter on /api/alerts reduces results."""
    response = client.get("/api/alerts?zone=Dan")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # 2 Tel Aviv + 1 Holon


def test_by_location_zone_filter(client):
    """Zone filter on /api/alerts/by-location reduces results."""
    response = client.get("/api/alerts/by-location?zone=Negev")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["location_name"] == "באר שבע"


def test_kpi_zone_filter(client):
    """Zone filter on /api/analytics/kpi reduces results."""
    response = client.get("/api/analytics/kpi?zone=Dan")
    assert response.status_code == 200
    data = response.json()
    assert data["total_alerts"] == 3
