from datetime import datetime

import pytest

from backend.models.alert import Alert
from backend.models.category import AlertCategory
from backend.models.location import Location


@pytest.fixture(autouse=True)
def seed_data(db_session):
    """Insert sample alerts before each test, clean up after."""
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
    ]
    db_session.add_all(alerts)
    db_session.commit()
    yield
    db_session.query(Alert).delete()
    db_session.query(Location).delete()
    db_session.query(AlertCategory).delete()
    db_session.commit()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_alerts(client):
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 4


def test_list_alerts_filter_by_category(client):
    response = client.get("/api/alerts?categories=1")
    data = response.json()
    assert data["total"] == 3
    assert all(item["category"] == 1 for item in data["items"])


def test_list_alerts_filter_by_location(client):
    response = client.get("/api/alerts?location=תל אביב")
    data = response.json()
    assert data["total"] == 2


def test_list_alerts_filter_by_date_range(client):
    response = client.get("/api/alerts?from_date=2024-01-01&to_date=2024-12-31")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["location_name"] == "באר שבע"


def test_list_alerts_pagination(client):
    response = client.get("/api/alerts?page=1&page_size=2")
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_timeline_daily(client):
    response = client.get("/api/alerts/timeline?granularity=day")
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "day"
    assert len(data["buckets"]) >= 1


def test_by_category(client):
    response = client.get("/api/alerts/by-category")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # category 1 and category 2
    assert data[0]["count"] >= data[1]["count"]  # sorted desc


def test_by_location(client):
    response = client.get("/api/alerts/by-location")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # תל אביב should be top (2 alerts)
    assert data[0]["location_name"] == "תל אביב"
    assert data[0]["count"] == 2


def test_hourly_heatmap(client):
    response = client.get("/api/analytics/hourly-heatmap")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for cell in data:
        assert 0 <= cell["hour"] <= 23
        assert 0 <= cell["weekday"] <= 6
        assert cell["count"] >= 1
    # Verify 0=Sunday convention: Oct 7 2023 is Saturday=6
    saturday_cells = [c for c in data if c["weekday"] == 6]
    assert len(saturday_cells) >= 1


def test_top_locations(client):
    response = client.get("/api/analytics/top-locations?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "sparkline" in data[0]
    assert "total" in data[0]


def test_kpi(client):
    response = client.get("/api/analytics/kpi")
    assert response.status_code == 200
    data = response.json()

    assert data["total_alerts"] == 4
    assert data["unique_locations"] == 3  # תל אביב, חולון, באר שבע

    # Peak day is 2023-10-07 with 3 alerts
    assert data["peak_day"]["date"] == "2023-10-07"
    assert data["peak_day"]["count"] == 3

    # Most active category is 1 (3 out of 4 = 75%)
    assert data["most_active_category"]["category"] == 1
    assert data["most_active_category"]["percentage"] == 75.0

    # Date range
    assert data["date_range"]["from"] == "2023-10-07"
    assert data["date_range"]["to"] == "2024-01-15"

    # Longest quiet: gap between 2023-10-07 and 2024-01-15 = 100 days
    assert data["longest_quiet_days"] == 100


def test_kpi_with_category_filter(client):
    response = client.get("/api/analytics/kpi?categories=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total_alerts"] == 1
    assert data["most_active_category"]["category"] == 2
    assert data["most_active_category"]["percentage"] == 100.0
    assert data["longest_quiet_days"] == 0  # only one day of alerts
