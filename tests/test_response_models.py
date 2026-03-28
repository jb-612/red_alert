"""Tests for response_model validation on endpoints (WI-3.2) and Field descriptions (WI-3.4)."""



from backend.schemas.alert import (
    AlertResponse,
    CategoryCount,
    HierarchyCity,
    HierarchyZone,
    LocationCount,
    TopLocationEntry,
)

# Reuse the same engine/session/client as test_api.py


# ---- WI-3.2: TopLocationEntry schema ----


def test_top_location_entry_schema():
    """TopLocationEntry has required fields: location_name, total, sparkline."""
    entry = TopLocationEntry(
        location_name="תל אביב",
        total=42,
        sparkline=[{"day": "2024-01-01", "count": 5}],
    )
    assert entry.location_name == "תל אביב"
    assert entry.total == 42
    assert len(entry.sparkline) == 1


def test_hierarchy_zone_schema():
    """HierarchyZone has required fields: zone, zone_en, total_alerts, cities."""
    city = HierarchyCity(
        name="תל אביב",
        name_en="Tel Aviv",
        lat=32.08,
        lng=34.78,
        alert_count=10,
    )
    zone = HierarchyZone(
        zone="דן",
        zone_en="Dan",
        total_alerts=10,
        cities=[city],
    )
    assert zone.zone == "דן"
    assert zone.zone_en == "Dan"
    assert len(zone.cities) == 1


def test_hierarchy_city_nullable_coords():
    """HierarchyCity allows None for lat/lng."""
    city = HierarchyCity(
        name="Unknown",
        name_en="Unknown",
        lat=None,
        lng=None,
        alert_count=0,
    )
    assert city.lat is None
    assert city.lng is None


# ---- WI-3.4: Field descriptions ----


def test_alert_response_field_descriptions():
    """AlertResponse fields should have descriptions."""
    schema = AlertResponse.model_json_schema()
    props = schema["properties"]
    for field_name in ("id", "alert_datetime", "location_name", "category", "source"):
        assert "description" in props[field_name], f"Missing description for {field_name}"


def test_category_count_field_descriptions():
    """CategoryCount fields should have descriptions."""
    schema = CategoryCount.model_json_schema()
    props = schema["properties"]
    for field_name in ("category", "category_desc", "count"):
        assert "description" in props[field_name], f"Missing description for {field_name}"


def test_location_count_field_descriptions():
    """LocationCount fields should have descriptions."""
    schema = LocationCount.model_json_schema()
    props = schema["properties"]
    for field_name in ("location_name", "count"):
        assert "description" in props[field_name], f"Missing description for {field_name}"
