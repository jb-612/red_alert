"""Tests for Phase 5 analytics: anomaly detection, period comparison, pre-alert correlation."""

from datetime import datetime

import pytest

from backend.models.alert import Alert
from tests.test_api import TestSession, client

# ---------------------------------------------------------------------------
# Seed data design for Phase 5:
#
# We need data that covers all three features: anomalies, comparison, correlation.
#
# ANOMALY DETECTION needs: days with varying alert counts, including a spike.
#   Jan 1-5: 2 alerts/day (normal baseline)
#   Jan 6: 20 alerts (spike = anomaly)
#   Jan 7-8: 2 alerts/day (back to normal)
#   → mean ≈ 3.5, stdev ≈ 6.0, Jan 6 z_score ≈ 2.7 (above threshold=2.0)
#
# PERIOD COMPARISON needs: two distinct periods with different profiles.
#   Period A: Jan 1-5 (10 alerts across 3 locations, cat 1)
#   Period B: Jan 6-10 (26 alerts, heavier in one location)
#
# PRE-ALERT CORRELATION needs: cat 14 followed by cat 1 at same location.
#   Feb 1 10:00 - cat 14 at תל אביב (followed by cat 1 at 10:15 = within 30min)
#   Feb 1 10:15 - cat 1  at תל אביב (match for above)
#   Feb 1 11:00 - cat 14 at חיפה    (NOT followed by cat 1 within 30min)
#   Feb 1 12:00 - cat 1  at חיפה    (60min later = outside 30min window)
#   Feb 1 14:00 - cat 14 at תל אביב (followed by cat 1 at 14:10)
#   Feb 1 14:10 - cat 1  at תל אביב (match)
#   Feb 1 15:00 - cat 14 at באר שבע  (followed by cat 1 at different location)
#   Feb 1 15:10 - cat 1  at תל אביב (wrong location for באר שבע pre-alert)
#
# Correlation results (window=30min):
#   תל אביב: 2 prealerts, 2 followed → probability = 1.0
#   חיפה: 1 prealert, 0 followed → probability = 0.0
#   באר שבע: 1 prealert, 0 followed → probability = 0.0
#   Overall: 4 prealerts, 2 followed → probability = 0.5
# ---------------------------------------------------------------------------


def _build_anomaly_alerts() -> list[Alert]:
    """Build alerts for anomaly detection: 5 normal days + 1 spike + 2 normal."""
    alerts: list[Alert] = []
    # Jan 1-5: 2 alerts per day (normal)
    for day in range(1, 6):
        for hour in [8, 14]:
            alerts.append(Alert(
                alert_datetime=datetime(2024, 1, day, hour, 0),
                location_name="תל אביב",
                category=1,
                category_desc="ירי רקטות וטילים",
                source="test",
            ))
    # Jan 6: 20 alerts (spike)
    for i in range(20):
        alerts.append(Alert(
            alert_datetime=datetime(2024, 1, 6, 6 + i // 4, (i % 4) * 15),
            location_name="תל אביב" if i % 2 == 0 else "חיפה",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ))
    # Jan 7-8: 2 alerts per day (normal)
    for day in [7, 8]:
        for hour in [8, 14]:
            alerts.append(Alert(
                alert_datetime=datetime(2024, 1, day, hour, 0),
                location_name="באר שבע",
                category=1,
                category_desc="ירי רקטות וטילים",
                source="test",
            ))
    return alerts


def _build_comparison_extra_alerts() -> list[Alert]:
    """Extra alerts for period B (Jan 6-10) to make comparison meaningful.

    Period A (Jan 1-5) already has alerts from _build_anomaly_alerts.
    Period B needs distinct profile — anomaly alerts cover Jan 6-8,
    add Jan 9-10 alerts with category 2.
    """
    alerts: list[Alert] = []
    for day in [9, 10]:
        for hour in [9, 15]:
            alerts.append(Alert(
                alert_datetime=datetime(2024, 1, day, hour, 0),
                location_name="חיפה",
                category=2,
                category_desc="חדירת כלי טיס עוין",
                source="test",
            ))
    return alerts


def _build_correlation_alerts() -> list[Alert]:
    """Build alerts for pre-alert correlation testing."""
    return [
        # Tel Aviv: cat 14 at 10:00, cat 1 at 10:15 → matched (within 30min)
        Alert(
            alert_datetime=datetime(2024, 2, 1, 10, 0),
            location_name="תל אביב",
            category=14,
            category_desc="הנחיה מקדימה",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 2, 1, 10, 15),
            location_name="תל אביב",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        # Haifa: cat 14 at 11:00, cat 1 at 12:00 → NOT matched (60min > 30min)
        Alert(
            alert_datetime=datetime(2024, 2, 1, 11, 0),
            location_name="חיפה",
            category=14,
            category_desc="הנחיה מקדימה",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 2, 1, 12, 0),
            location_name="חיפה",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        # Tel Aviv: cat 14 at 14:00, cat 1 at 14:10 → matched
        Alert(
            alert_datetime=datetime(2024, 2, 1, 14, 0),
            location_name="תל אביב",
            category=14,
            category_desc="הנחיה מקדימה",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 2, 1, 14, 10),
            location_name="תל אביב",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
        # Beer Sheva: cat 14 at 15:00, cat 1 at different location → NOT matched
        Alert(
            alert_datetime=datetime(2024, 2, 1, 15, 0),
            location_name="באר שבע",
            category=14,
            category_desc="הנחיה מקדימה",
            source="test",
        ),
        Alert(
            alert_datetime=datetime(2024, 2, 1, 15, 10),
            location_name="תל אביב",
            category=1,
            category_desc="ירי רקטות וטילים",
            source="test",
        ),
    ]


@pytest.fixture(autouse=True)
def seed_data():
    """Insert Phase 5 test alerts, clean up after."""
    db = TestSession()
    all_alerts = (
        _build_anomaly_alerts()
        + _build_comparison_extra_alerts()
        + _build_correlation_alerts()
    )
    db.add_all(all_alerts)
    db.commit()
    yield
    db.query(Alert).delete()
    db.commit()
    db.close()


# ===================== Anomaly Detection =====================


class TestAnomalyDetection:
    """Tests for GET /api/analytics/anomalies."""

    def test_anomaly_basic_structure(self):
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-08"
        )
        assert r.status_code == 200
        data = r.json()
        assert "mean_daily_count" in data
        assert "std_daily_count" in data
        assert "threshold" in data
        assert "total_days_analyzed" in data
        assert "anomalies" in data

    def test_anomaly_detects_spike(self):
        """Jan 6 has 20 alerts vs ~2/day baseline → detected as 'high'."""
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-08"
        )
        data = r.json()
        anomalies = data["anomalies"]
        spike = next((a for a in anomalies if a["date"] == "2024-01-06"), None)
        assert spike is not None
        assert spike["direction"] == "high"
        assert spike["z_score"] > 2.0

    def test_anomaly_threshold_parameter(self):
        """Lower threshold finds more anomalies."""
        r_strict = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-08&threshold=3.0"
        )
        r_loose = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-08&threshold=1.0"
        )
        strict = r_strict.json()["anomalies"]
        loose = r_loose.json()["anomalies"]
        assert len(loose) >= len(strict)

    def test_anomaly_uniform_no_anomalies(self):
        """Jan 1-5 all have 2 alerts → stdev=0 → no anomalies."""
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-05"
        )
        data = r.json()
        assert data["std_daily_count"] == 0.0
        assert len(data["anomalies"]) == 0

    def test_anomaly_insufficient_data(self):
        """Single day → stdev undefined → no anomalies."""
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-01"
        )
        data = r.json()
        assert len(data["anomalies"]) == 0

    def test_anomaly_with_category_filter(self):
        """Category filter scopes daily counts."""
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-10&categories=2"
        )
        data = r.json()
        # Category 2 only has alerts on Jan 9-10 (2/day), uniform → no anomalies
        assert data["std_daily_count"] == 0.0
        assert len(data["anomalies"]) == 0

    def test_anomaly_with_location_filter(self):
        """Location filter scopes daily counts."""
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-08"
            "&location=באר שבע"
        )
        data = r.json()
        # Beer Sheva only has alerts on Jan 7-8 (2/day), uniform
        assert data["std_daily_count"] == 0.0

    def test_anomaly_sorted_by_zscore(self):
        """Anomalies sorted by |z_score| descending."""
        r = client.get(
            "/api/analytics/anomalies"
            "?from_date=2024-01-01&to_date=2024-01-08&threshold=1.0"
        )
        data = r.json()
        if len(data["anomalies"]) > 1:
            z_scores = [abs(a["z_score"]) for a in data["anomalies"]]
            assert z_scores == sorted(z_scores, reverse=True)


# ===================== Period Comparison =====================


class TestPeriodComparison:
    """Tests for GET /api/analytics/compare."""

    def test_compare_basic_structure(self):
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2024-01-01&period_a_to=2024-01-05"
            "&period_b_from=2024-01-06&period_b_to=2024-01-10"
        )
        assert r.status_code == 200
        data = r.json()
        assert "period_a" in data
        assert "period_b" in data
        assert "delta" in data
        for period in [data["period_a"], data["period_b"]]:
            assert "total_alerts" in period
            assert "unique_locations" in period
            assert "top_categories" in period
            assert "top_locations" in period
            assert "timeline" in period

    def test_compare_delta_positive(self):
        """Period B (Jan 6-10) has more alerts than period A (Jan 1-5)."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2024-01-01&period_a_to=2024-01-05"
            "&period_b_from=2024-01-06&period_b_to=2024-01-10"
        )
        data = r.json()
        assert data["delta"]["total_alerts_delta"] > 0
        assert data["delta"]["total_alerts_pct"] is not None
        assert data["delta"]["total_alerts_pct"] > 0

    def test_compare_delta_negative(self):
        """Swap periods → negative delta."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2024-01-06&period_a_to=2024-01-10"
            "&period_b_from=2024-01-01&period_b_to=2024-01-05"
        )
        data = r.json()
        assert data["delta"]["total_alerts_delta"] < 0

    def test_compare_zero_division(self):
        """Period A has 0 alerts → delta_pct is None."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2025-06-01&period_a_to=2025-06-05"
            "&period_b_from=2024-01-01&period_b_to=2024-01-05"
        )
        data = r.json()
        assert data["period_a"]["total_alerts"] == 0
        assert data["delta"]["total_alerts_pct"] is None

    def test_compare_both_empty(self):
        """Both periods empty → all zeros."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2025-06-01&period_a_to=2025-06-05"
            "&period_b_from=2025-07-01&period_b_to=2025-07-05"
        )
        data = r.json()
        assert data["period_a"]["total_alerts"] == 0
        assert data["period_b"]["total_alerts"] == 0
        assert data["delta"]["total_alerts_delta"] == 0

    def test_compare_with_category_filter(self):
        """Category filter applied to both periods."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2024-01-01&period_a_to=2024-01-05"
            "&period_b_from=2024-01-06&period_b_to=2024-01-10"
            "&categories=2"
        )
        data = r.json()
        # Cat 2 only in period B (Jan 9-10, 4 alerts)
        assert data["period_a"]["total_alerts"] == 0
        assert data["period_b"]["total_alerts"] == 4

    def test_compare_with_location_filter(self):
        """Location filter applied to both periods."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2024-01-01&period_a_to=2024-01-05"
            "&period_b_from=2024-01-06&period_b_to=2024-01-10"
            "&location=חיפה"
        )
        data = r.json()
        # Haifa: 0 in period A (Jan 1-5 only has Tel Aviv),
        # some in period B (Jan 6 spike + Jan 9-10)
        assert data["period_a"]["total_alerts"] == 0
        assert data["period_b"]["total_alerts"] > 0

    def test_compare_timeline_within_bounds(self):
        """Timeline buckets fall within respective period bounds."""
        r = client.get(
            "/api/analytics/compare"
            "?period_a_from=2024-01-01&period_a_to=2024-01-05"
            "&period_b_from=2024-01-06&period_b_to=2024-01-10"
        )
        data = r.json()
        for bucket in data["period_a"]["timeline"]:
            assert bucket["period"] >= "2024-01-01"
            assert bucket["period"] <= "2024-01-05"


# ===================== Pre-alert Correlation =====================


class TestPrealertCorrelation:
    """Tests for GET /api/analytics/prealert-correlation."""

    def test_prealert_basic_structure(self):
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
        )
        assert r.status_code == 200
        data = r.json()
        assert "window_minutes" in data
        assert "overall_total_prealerts" in data
        assert "overall_followed" in data
        assert "overall_probability" in data
        assert "locations" in data

    def test_prealert_match_within_window(self):
        """Tel Aviv: 2 prealerts, both followed by cat 1 within 30min."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
            "&min_prealerts=1"
        )
        data = r.json()
        ta = next(
            (loc for loc in data["locations"] if loc["location_name"] == "תל אביב"),
            None,
        )
        assert ta is not None
        assert ta["total_prealerts"] == 2
        assert ta["followed_by_actual"] == 2
        assert ta["probability"] == 1.0

    def test_prealert_no_match_outside_window(self):
        """Haifa: cat 14 at 11:00, cat 1 at 12:00 → 60min > 30min window."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
            "&window_minutes=30&min_prealerts=1"
        )
        data = r.json()
        haifa = next(
            (loc for loc in data["locations"] if loc["location_name"] == "חיפה"),
            None,
        )
        assert haifa is not None
        assert haifa["followed_by_actual"] == 0
        assert haifa["probability"] == 0.0

    def test_prealert_same_location_required(self):
        """Beer Sheva: cat 14 at 15:00, but cat 1 at 15:10 is Tel Aviv → no match."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
            "&min_prealerts=1"
        )
        data = r.json()
        bs = next(
            (loc for loc in data["locations"] if loc["location_name"] == "באר שבע"),
            None,
        )
        assert bs is not None
        assert bs["followed_by_actual"] == 0
        assert bs["probability"] == 0.0

    def test_prealert_overall_probability(self):
        """Overall: 4 prealerts, 2 followed → 0.5."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
            "&min_prealerts=1"
        )
        data = r.json()
        assert data["overall_total_prealerts"] == 4
        assert data["overall_followed"] == 2
        assert data["overall_probability"] == 0.5

    def test_prealert_min_prealerts_filter(self):
        """min_prealerts=2 excludes Haifa (1) and Beer Sheva (1)."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
            "&min_prealerts=2"
        )
        data = r.json()
        names = [loc["location_name"] for loc in data["locations"]]
        assert "תל אביב" in names
        assert "חיפה" not in names
        assert "באר שבע" not in names

    def test_prealert_wider_window_finds_more(self):
        """window=60 should match Haifa (60min gap) too."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2024-02-01&to_date=2024-02-28"
            "&window_minutes=60&min_prealerts=1"
        )
        data = r.json()
        haifa = next(
            (loc for loc in data["locations"] if loc["location_name"] == "חיפה"),
            None,
        )
        assert haifa is not None
        assert haifa["followed_by_actual"] == 1
        assert haifa["probability"] == 1.0
        # Overall should now be 3/4 = 0.75
        assert data["overall_followed"] == 3

    def test_prealert_empty_range(self):
        """No cat 14 alerts in range → empty response."""
        r = client.get(
            "/api/analytics/prealert-correlation"
            "?from_date=2025-06-01&to_date=2025-06-30"
        )
        data = r.json()
        assert data["overall_total_prealerts"] == 0
        assert data["overall_probability"] == 0.0
        assert len(data["locations"]) == 0
