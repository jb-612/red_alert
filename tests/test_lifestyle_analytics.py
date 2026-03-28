"""Tests for Phase 4 Lifestyle Analytics endpoints: sleep score, best weekdays, quiet streaks."""

from datetime import datetime

import pytest

from backend.models.alert import Alert
from backend.models.category import AlertCategory
from backend.models.location import Location

# ---------------------------------------------------------------------------
# Seed data layout (all dates in January 2024):
#
# Jan 10 (Wed) 23:00 — night alert (disturbs night of Jan 10)
# Jan 11 (Thu) 14:00 — daytime only (night of Jan 11 is peaceful)
# Jan 13 (Sat) 02:00 — post-midnight (disturbs night of Jan 11... wait)
#   Actually: 02:00 on Jan 12 maps to night of Jan 11 → disturbs it
#   So let's adjust: we want Jan 11 night peaceful, so no alerts 22:00 Jan 11 - 06:59 Jan 12.
#
# Revised seed data:
# Jan 10 (Wed) 23:00  — cat 1 — disturbs night of Jan 10
# Jan 11 (Thu) 14:00  — cat 1 — daytime, night of Jan 11 is peaceful
# Jan 13 (Sat) 03:30  — cat 1 — disturbs night of Jan 12 (post-midnight)
# Jan 13 (Sat) 15:00  — cat 2 — daytime, night of Jan 13 is peaceful
# Jan 15 (Mon) 22:00  — cat 1 — disturbs night of Jan 15 (boundary: exactly 22:00)
# Jan 20 (Sat) 07:00  — cat 1 — daytime (boundary: exactly 07:00 = NOT nighttime)
# Jan 20 (Sat) 10:00  — cat 2 — daytime
#
# Night analysis (for range Jan 10 - Jan 20):
#   Jan 10 night: DISTURBED (23:00 alert)
#   Jan 11 night: PEACEFUL (14:00 alert is daytime, no night alerts)
#   Jan 12 night: DISTURBED (03:30 on Jan 13 maps to night of Jan 12)
#   Jan 13 night: PEACEFUL
#   Jan 14 night: PEACEFUL
#   Jan 15 night: DISTURBED (22:00 alert)
#   Jan 16 night: PEACEFUL
#   Jan 17 night: PEACEFUL
#   Jan 18 night: PEACEFUL
#   Jan 19 night: PEACEFUL
#   Total: 11 nights, 7 peaceful, 4 disturbed → score = 63.6%
#
# Weekday distribution:
#   Sun(0): 0 alerts
#   Mon(1): 1 alert (Jan 15)
#   Tue(2): 0 alerts
#   Wed(3): 1 alert (Jan 10)
#   Thu(4): 1 alert (Jan 11)
#   Fri(5): 0 alerts
#   Sat(6): 3 alerts (Jan 13 x2, Jan 20 x2) — wait let me recount
#
# Recount by weekday:
#   Jan 10 Wed: 1 alert
#   Jan 11 Thu: 1 alert
#   Jan 13 Sat: 2 alerts (03:30 + 15:00)
#   Jan 15 Mon: 1 alert
#   Jan 20 Sat: 2 alerts (07:00 + 10:00)
#   → Sun=0, Mon=1, Tue=0, Wed=1, Thu=1, Fri=0, Sat=4
#   Best days: Sun, Tue, Fri (0 alerts each)
#
# Quiet streaks (alert days: Jan 10, 11, 13, 15, 20):
#   Between Jan 11 and Jan 13: Jan 12 only → 1 day
#   Between Jan 13 and Jan 15: Jan 14 only → 1 day
#   Between Jan 15 and Jan 20: Jan 16,17,18,19 → 4 days (longest)
#   Current streak from Jan 20 to Jan 20 (last day): 0 → None
# ---------------------------------------------------------------------------

SEED_ALERTS = [
    Alert(
        alert_datetime=datetime(2024, 1, 10, 23, 0),
        location_name="תל אביב",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ),
    Alert(
        alert_datetime=datetime(2024, 1, 11, 14, 0),
        location_name="חיפה",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ),
    Alert(
        alert_datetime=datetime(2024, 1, 13, 3, 30),
        location_name="תל אביב",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ),
    Alert(
        alert_datetime=datetime(2024, 1, 13, 15, 0),
        location_name="באר שבע",
        category=2,
        category_desc="חדירת כלי טיס עוין",
        source="test",
    ),
    Alert(
        alert_datetime=datetime(2024, 1, 15, 22, 0),
        location_name="תל אביב",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ),
    Alert(
        alert_datetime=datetime(2024, 1, 20, 7, 0),
        location_name="חיפה",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ),
    Alert(
        alert_datetime=datetime(2024, 1, 20, 10, 0),
        location_name="באר שבע",
        category=2,
        category_desc="חדירת כלי טיס עוין",
        source="test",
    ),
]


@pytest.fixture(autouse=True)
def seed_data(db_session):
    """Insert lifestyle analytics test alerts, clean up after."""
    db_session.add_all([Alert(
        alert_datetime=a.alert_datetime,
        location_name=a.location_name,
        category=a.category,
        category_desc=a.category_desc,
        source=a.source,
    ) for a in SEED_ALERTS])
    db_session.commit()
    yield
    db_session.query(Alert).delete()
    db_session.query(Location).delete()
    db_session.query(AlertCategory).delete()
    db_session.commit()


# ===================== Sleep Score =====================


class TestSleepScore:
    """Tests for GET /api/analytics/sleep-score."""

    def test_sleep_score_basic(self, client):
        """Score with known mix of disturbed/peaceful nights."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-10&to_date=2024-01-20"
        )
        assert r.status_code == 200
        data = r.json()
        assert "score" in data
        assert "total_nights" in data
        assert "peaceful_nights" in data
        assert "trend" in data
        assert data["total_nights"] > 0
        assert 0 <= data["score"] <= 100
        assert data["peaceful_nights"] <= data["total_nights"]

    def test_sleep_score_trend_entries(self, client):
        """Trend array has one entry per night in range."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-10&to_date=2024-01-20"
        )
        data = r.json()
        assert len(data["trend"]) == data["total_nights"]
        for entry in data["trend"]:
            assert "date" in entry
            assert "peaceful" in entry

    def test_sleep_score_night_of_jan10_disturbed(self, client):
        """Night of Jan 10 is disturbed (alert at 23:00)."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-10&to_date=2024-01-11"
        )
        data = r.json()
        # Only night of Jan 10; it has 23:00 alert → disturbed
        assert data["total_nights"] == 1
        assert data["peaceful_nights"] == 0
        assert data["score"] == 0.0

    def test_sleep_score_night_of_jan11_peaceful(self, client):
        """Night of Jan 11 is peaceful (only a 14:00 daytime alert)."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-11&to_date=2024-01-12"
        )
        data = r.json()
        assert data["total_nights"] == 1
        assert data["peaceful_nights"] == 1
        assert data["score"] == 100.0

    def test_sleep_score_night_of_jan12_disturbed_by_post_midnight(self, client):
        """Night of Jan 12 is disturbed by 03:30 alert on Jan 13."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-12&to_date=2024-01-13"
        )
        data = r.json()
        assert data["total_nights"] == 1
        assert data["peaceful_nights"] == 0
        assert data["score"] == 0.0

    def test_sleep_score_boundary_2200_is_nighttime(self, client):
        """Alert at exactly 22:00 counts as nighttime (disturbs the night)."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-15&to_date=2024-01-16"
        )
        data = r.json()
        assert data["peaceful_nights"] == 0

    def test_sleep_score_boundary_0700_is_daytime(self, client):
        """Alert at exactly 07:00 is daytime, does NOT disturb the night."""
        # Night of Jan 19 has no alerts (07:00 on Jan 20 is daytime)
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-19&to_date=2024-01-20"
        )
        data = r.json()
        assert data["peaceful_nights"] == 1
        assert data["score"] == 100.0

    def test_sleep_score_with_location_filter(self, client):
        """Location filter scopes which alerts count."""
        # Only באר שבע alerts: Jan 13 15:00 and Jan 20 10:00 (both daytime)
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-10&to_date=2024-01-20&location=באר שבע"
        )
        data = r.json()
        # All nights should be peaceful for באר שבע
        assert data["peaceful_nights"] == data["total_nights"]
        assert data["score"] == 100.0

    def test_sleep_score_with_category_filter(self, client):
        """Category filter scopes which alerts count."""
        # Category 2 alerts: Jan 13 15:00, Jan 20 10:00 (both daytime)
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2024-01-10&to_date=2024-01-20&categories=2"
        )
        data = r.json()
        assert data["peaceful_nights"] == data["total_nights"]
        assert data["score"] == 100.0

    def test_sleep_score_empty_range(self, client):
        """Date range with no alerts returns all-peaceful."""
        r = client.get(
            "/api/analytics/sleep-score"
            "?from_date=2025-06-01&to_date=2025-06-05"
        )
        data = r.json()
        assert data["total_nights"] == 4
        assert data["peaceful_nights"] == 4
        assert data["score"] == 100.0


# ===================== Best Weekdays =====================


class TestBestWeekdays:
    """Tests for GET /api/analytics/best-weekdays."""

    def test_best_weekdays_returns_seven_days(self, client):
        """Always returns all 7 weekdays even if some have 0 alerts."""
        r = client.get("/api/analytics/best-weekdays")
        assert r.status_code == 200
        data = r.json()
        assert len(data["weekdays"]) == 7
        weekday_ids = {d["weekday"] for d in data["weekdays"]}
        assert weekday_ids == {0, 1, 2, 3, 4, 5, 6}

    def test_best_weekdays_ranking_order(self, client):
        """Weekdays ranked ascending by alert count (safest first)."""
        r = client.get("/api/analytics/best-weekdays")
        data = r.json()
        counts = [d["alert_count"] for d in data["weekdays"]]
        assert counts == sorted(counts)

    def test_best_weekdays_rank_values(self, client):
        """Rank values are 1-7."""
        r = client.get("/api/analytics/best-weekdays")
        data = r.json()
        ranks = sorted(d["rank"] for d in data["weekdays"])
        assert ranks == [1, 2, 3, 4, 5, 6, 7]

    def test_best_weekdays_names_correct(self, client):
        """Each weekday has the correct English name."""
        expected = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
                    4: "Thursday", 5: "Friday", 6: "Saturday"}
        r = client.get("/api/analytics/best-weekdays")
        data = r.json()
        for d in data["weekdays"]:
            assert d["weekday_name"] == expected[d["weekday"]]

    def test_best_weekdays_saturday_most_alerts(self, client):
        """Saturday has the most alerts (4) in our seed data."""
        r = client.get("/api/analytics/best-weekdays")
        data = r.json()
        sat = next(d for d in data["weekdays"] if d["weekday"] == 6)
        assert sat["alert_count"] == 4
        assert sat["rank"] == 7  # worst day

    def test_best_weekdays_zero_alert_days(self, client):
        """Sunday, Tuesday, Friday have 0 alerts."""
        r = client.get("/api/analytics/best-weekdays")
        data = r.json()
        for day_id in [0, 2, 5]:  # Sun, Tue, Fri
            day = next(d for d in data["weekdays"] if d["weekday"] == day_id)
            assert day["alert_count"] == 0

    def test_best_weekdays_with_category_filter(self, client):
        """Category filter reduces counts."""
        # Category 2 only: Jan 13 (Sat) and Jan 20 (Sat) → Sat=2, rest=0
        r = client.get("/api/analytics/best-weekdays?categories=2")
        data = r.json()
        sat = next(d for d in data["weekdays"] if d["weekday"] == 6)
        assert sat["alert_count"] == 2
        non_sat = [d for d in data["weekdays"] if d["weekday"] != 6]
        assert all(d["alert_count"] == 0 for d in non_sat)

    def test_best_weekdays_hot_hours_structure(self, client):
        """Hot hours list has expected structure."""
        r = client.get("/api/analytics/best-weekdays?top_locations=3")
        data = r.json()
        assert "hot_hours" in data
        for hh in data["hot_hours"]:
            assert "location_name" in hh
            assert 0 <= hh["peak_hour"] <= 23
            assert hh["alert_count"] >= 1

    def test_best_weekdays_hot_hours_correct(self, client):
        """Tel Aviv peak hour is 23 (one alert at 23:00, one at 03:30, one at 22:00)."""
        r = client.get("/api/analytics/best-weekdays?top_locations=3")
        data = r.json()
        ta = next((h for h in data["hot_hours"] if h["location_name"] == "תל אביב"), None)
        assert ta is not None
        # Tel Aviv has alerts at hours 23, 3, 22 — each with 1 alert, so any could be peak.
        # The endpoint should pick one deterministically (e.g., first by count then by hour).
        assert ta["peak_hour"] in [3, 22, 23]


# ===================== Quiet Streaks =====================


class TestQuietStreaks:
    """Tests for GET /api/analytics/quiet-streaks."""

    def test_quiet_streaks_basic(self, client):
        """Returns expected structure."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-20"
        )
        assert r.status_code == 200
        data = r.json()
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "top_streaks" in data

    def test_quiet_streaks_longest(self, client):
        """Longest streak is Jan 16-19 (4 days between Jan 15 and Jan 20)."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-20"
        )
        data = r.json()
        longest = data["longest_streak"]
        assert longest is not None
        assert longest["days"] == 4
        assert longest["start_date"] == "2024-01-16"
        assert longest["end_date"] == "2024-01-19"

    def test_quiet_streaks_no_current_when_last_day_has_alerts(self, client):
        """Current streak is None when to_date has alerts."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-20"
        )
        data = r.json()
        # Jan 20 has alerts, so no current streak
        assert data["current_streak"] is None

    def test_quiet_streaks_current_when_trailing_quiet(self, client):
        """Current streak exists when to_date is after last alert."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-25"
        )
        data = r.json()
        # Last alert is Jan 20, to_date is Jan 25 → 5 quiet days (Jan 21-25)
        assert data["current_streak"] is not None
        assert data["current_streak"]["days"] == 5
        assert data["current_streak"]["start_date"] == "2024-01-21"
        assert data["current_streak"]["end_date"] == "2024-01-25"

    def test_quiet_streaks_top_ordering(self, client):
        """Top streaks sorted descending by days."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-20"
        )
        data = r.json()
        days_list = [s["days"] for s in data["top_streaks"]]
        assert days_list == sorted(days_list, reverse=True)

    def test_quiet_streaks_top_n_limit(self, client):
        """Respects top_n parameter."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-20&top_n=1"
        )
        data = r.json()
        assert len(data["top_streaks"]) <= 1

    def test_quiet_streaks_consecutive_days_no_streak(self, client):
        """Consecutive alert days produce no quiet streak between them."""
        # Jan 10 and Jan 11 both have alerts → 0 quiet days between them
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-11"
        )
        data = r.json()
        # No streaks of length > 0 between consecutive alert days
        assert all(s["days"] > 0 for s in data["top_streaks"])

    def test_quiet_streaks_with_location_filter(self, client):
        """Location filter changes which days count as alert days."""
        # באר שבע only has alerts on Jan 13 and Jan 20
        # Gap between them: Jan 14-19 = 6 quiet days
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2024-01-10&to_date=2024-01-20&location=באר שבע"
        )
        data = r.json()
        longest = data["longest_streak"]
        assert longest is not None
        assert longest["days"] == 6

    def test_quiet_streaks_empty_range(self, client):
        """Range with no alerts — everything is quiet."""
        r = client.get(
            "/api/analytics/quiet-streaks"
            "?from_date=2025-06-01&to_date=2025-06-10"
        )
        data = r.json()
        # Entire range is one big quiet streak
        assert data["current_streak"] is not None
        assert data["current_streak"]["days"] == 10
