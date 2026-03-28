"""Tests for geo endpoints, location hierarchy, and by-region analytics."""

import json
import tempfile
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.ingestion.locations_loader import load_locations
from backend.models.alert import Alert
from backend.models.location import Location

# Reuse the same engine/session/client as test_api.py to avoid
# conflicting app.dependency_overrides[get_db] at module level.
from tests.test_api import TestSession, client

SAMPLE_CITIES = [
    {
        "id": 0,
        "name": "בחר הכל",
        "name_en": "Select All",
        "zone": "",
        "zone_en": "",
        "countdown": 0,
        "lat": 0,
        "lng": 0,
        "value": "all",
    },
    {
        "id": 1,
        "name": "תל אביב",
        "name_en": "Tel Aviv",
        "zone": "דן",
        "zone_en": "Dan",
        "countdown": 90,
        "lat": 32.0853,
        "lng": 34.7818,
    },
    {
        "id": 2,
        "name": "חולון",
        "name_en": "Holon",
        "zone": "דן",
        "zone_en": "Dan",
        "countdown": 90,
        "lat": 32.0114,
        "lng": 34.7748,
    },
    {
        "id": 3,
        "name": "באר שבע",
        "name_en": "Be'er Sheva",
        "zone": "נגב",
        "zone_en": "Negev",
        "countdown": 60,
        "lat": 31.2518,
        "lng": 34.7913,
    },
    {
        "id": 4,
        "name": "אשדוד",
        "name_en": "Ashdod",
        "zone": "לכיש",
        "zone_en": "Lakhish",
        "countdown": 45,
        "lat": 31.8040,
        "lng": 34.6553,
    },
]


@pytest.fixture(autouse=True)
def seed_data():
    """Insert sample locations and alerts before each test, clean up after."""
    db = TestSession()

    # Insert locations
    for city in SAMPLE_CITIES:
        if city["name"] == "בחר הכל":
            continue
        db.add(Location(
            name=city["name"],
            name_en=city["name_en"],
            zone=city["zone"],
            zone_en=city["zone_en"],
            latitude=city["lat"],
            longitude=city["lng"],
            countdown_sec=city["countdown"],
        ))

    # Insert alerts
    alerts = [
        Alert(
            alert_datetime=datetime(2023, 10, 7, 6, 30),
            location_name="תל אביב",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2023, 10, 7, 6, 31),
            location_name="חולון",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2023, 10, 7, 7, 0),
            location_name="תל אביב",
            category=2,
            category_desc="חדירת כלי טיס עוין",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 1, 15, 10, 30),
            location_name="באר שבע",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 1, 16, 11, 0),
            location_name="אשדוד",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
    ]
    db.add_all(alerts)
    db.commit()
    yield
    db.query(Alert).delete()
    db.query(Location).delete()
    db.commit()
    db.close()


# ---- Location Loader Tests ----


def test_load_locations_from_json():
    """Test that the location loader parses cities.json correctly."""
    db = TestSession()
    # Clean existing locations from seed
    db.query(Location).delete()
    db.commit()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(SAMPLE_CITIES, f)
        f.flush()
        count = load_locations(db, f.name)

    assert count == 4  # Skips "בחר הכל"

    loc = db.query(Location).filter_by(name="תל אביב").first()
    assert loc is not None
    assert loc.name_en == "Tel Aviv"
    assert loc.zone_en == "Dan"
    assert float(loc.latitude) == pytest.approx(32.0853, abs=0.001)

    db.query(Location).delete()
    db.commit()
    db.close()


def test_load_locations_skips_zero_coords():
    """Locations with lat=0, lng=0 are skipped."""
    db = TestSession()
    db.query(Location).delete()
    db.commit()

    cities = [
        {"id": 99, "name": "NoCoords", "name_en": "No", "zone": "X", "zone_en": "X",
         "countdown": 0, "lat": 0, "lng": 0},
        {"id": 100, "name": "HasCoords", "name_en": "Has", "zone": "X", "zone_en": "X",
         "countdown": 30, "lat": 31.0, "lng": 34.0},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cities, f)
        f.flush()
        count = load_locations(db, f.name)

    assert count == 1
    db.query(Location).delete()
    db.commit()
    db.close()


def test_load_locations_upsert():
    """Loading the same data twice should update, not duplicate."""
    db = TestSession()
    db.query(Location).delete()
    db.commit()

    cities = [
        {"id": 1, "name": "TestCity", "name_en": "V1", "zone": "Z", "zone_en": "Z",
         "countdown": 30, "lat": 31.0, "lng": 34.0},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cities, f)
        f.flush()
        load_locations(db, f.name)

    # Update the name_en
    cities[0]["name_en"] = "V2"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cities, f)
        f.flush()
        load_locations(db, f.name)

    locs = db.query(Location).filter_by(name="TestCity").all()
    assert len(locs) == 1
    assert locs[0].name_en == "V2"

    db.query(Location).delete()
    db.commit()
    db.close()


# ---- GET /api/alerts/geo Tests ----


def test_geo_endpoint_returns_locations():
    response = client.get("/api/alerts/geo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4  # 4 locations with alerts + coordinates
    names = {p["location_name"] for p in data}
    assert "תל אביב" in names
    assert "באר שבע" in names


def test_geo_endpoint_has_correct_structure():
    response = client.get("/api/alerts/geo")
    data = response.json()
    for point in data:
        assert "location_name" in point
        assert "lat" in point
        assert "lng" in point
        assert "count" in point
        assert "categories" in point
        assert isinstance(point["categories"], list)


def test_geo_endpoint_tel_aviv_count():
    response = client.get("/api/alerts/geo")
    data = response.json()
    tel_aviv = next(p for p in data if p["location_name"] == "תל אביב")
    assert tel_aviv["count"] == 2
    assert sorted(tel_aviv["categories"]) == [1, 2]


def test_geo_endpoint_filter_by_category():
    response = client.get("/api/alerts/geo?categories=2")
    data = response.json()
    # Only Tel Aviv has category 2 alerts
    assert len(data) == 1
    assert data[0]["location_name"] == "תל אביב"
    assert data[0]["count"] == 1


def test_geo_endpoint_filter_by_date():
    response = client.get("/api/alerts/geo?from_date=2024-01-01")
    data = response.json()
    names = {p["location_name"] for p in data}
    assert "תל אביב" not in names  # Only 2023 alerts
    assert "באר שבע" in names


# ---- GET /api/locations/hierarchy Tests ----


def test_hierarchy_returns_zones():
    response = client.get("/api/locations/hierarchy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Dan, Negev, Lakhish
    zone_names = {z["zone_en"] for z in data}
    assert "Dan" in zone_names
    assert "Negev" in zone_names
    assert "Lakhish" in zone_names


def test_hierarchy_has_cities():
    response = client.get("/api/locations/hierarchy")
    data = response.json()
    dan = next(z for z in data if z["zone_en"] == "Dan")
    assert len(dan["cities"]) == 2
    city_names = {c["name_en"] for c in dan["cities"]}
    assert "Tel Aviv" in city_names
    assert "Holon" in city_names


def test_hierarchy_sorted_by_alert_count():
    response = client.get("/api/locations/hierarchy")
    data = response.json()
    # Dan zone has 3 alerts total, should be first
    assert data[0]["zone_en"] == "Dan"
    assert data[0]["total_alerts"] == 3


def test_hierarchy_city_alert_counts():
    response = client.get("/api/locations/hierarchy")
    data = response.json()
    dan = next(z for z in data if z["zone_en"] == "Dan")
    # Cities sorted by alert count desc within zone
    assert dan["cities"][0]["name"] == "תל אביב"
    assert dan["cities"][0]["alert_count"] == 2
    assert dan["cities"][1]["name"] == "חולון"
    assert dan["cities"][1]["alert_count"] == 1


# ---- GET /api/analytics/by-region/{zone_en} Tests ----


def test_by_region_dan():
    response = client.get("/api/analytics/by-region/Dan")
    assert response.status_code == 200
    data = response.json()
    assert data["zone_en"] == "Dan"
    assert data["total_alerts"] == 3  # 2 Tel Aviv + 1 Holon
    assert len(data["top_locations"]) >= 1
    assert len(data["category_breakdown"]) >= 1
    assert len(data["timeline"]) >= 1


def test_by_region_negev():
    response = client.get("/api/analytics/by-region/Negev")
    data = response.json()
    assert data["total_alerts"] == 1
    assert data["top_locations"][0]["location_name"] == "באר שבע"


def test_by_region_nonexistent():
    response = client.get("/api/analytics/by-region/Nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["total_alerts"] == 0
    assert data["top_locations"] == []
    assert data["category_breakdown"] == []
    assert data["timeline"] == []


def test_by_region_filter_by_date():
    response = client.get("/api/analytics/by-region/Dan?from_date=2024-01-01")
    data = response.json()
    assert data["total_alerts"] == 0  # Dan alerts are all from 2023


def test_by_region_category_breakdown():
    response = client.get("/api/analytics/by-region/Dan")
    data = response.json()
    cats = {c["category"]: c["count"] for c in data["category_breakdown"]}
    assert cats[1] == 2  # 2 rocket alerts (Tel Aviv + Holon)
    assert cats[2] == 1  # 1 aircraft alert (Tel Aviv)


def test_by_region_timeline():
    response = client.get("/api/analytics/by-region/Dan")
    data = response.json()
    assert len(data["timeline"]) == 1  # All Dan alerts on 2023-10-07
    assert data["timeline"][0]["period"] == "2023-10-07"
    assert data["timeline"][0]["count"] == 3
