"""Tests for the ACLED aggregate (Explorer static file) ingestion client."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Iterator

from backend.database import Base
from backend.ingestion.acled_aggregate_client import (
    AGGREGATE_BASE_URL,
    DISORDER_VARIANTS,
    TIME_TO_GRANULARITY,
    TIME_VARIANTS,
    AggregateRow,
    aggregate_url,
    classify_country_theater,
    parse_overview,
    upsert_aggregates,
)
from backend.models.acled_aggregate import AcledAggregate

FIXTURE_DIR = Path(__file__).parent / "fixtures"
YEAR_ALL_FIXTURE = FIXTURE_DIR / "acled_year_all_overview.json"
WEEK_ALL_FIXTURE = FIXTURE_DIR / "acled_week_all_overview.json"
MONTH_ALL_FIXTURE = FIXTURE_DIR / "acled_month_all_overview.json"
YEAR_PV_FIXTURE = FIXTURE_DIR / "acled_year_politicalviolence_overview.json"


@pytest.fixture()
def db() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


class TestUrlBuilder:
    def test_aggregate_url_year_all(self) -> None:
        url = aggregate_url("year", "all")
        assert url == f"{AGGREGATE_BASE_URL}year_all_overview.json"

    def test_aggregate_url_week_politicalviolence(self) -> None:
        url = aggregate_url("week", "politicalviolence")
        assert url.endswith("week_politicalviolence_overview.json")


class TestTimeToGranularity:
    def test_year_maps_to_month(self) -> None:
        assert TIME_TO_GRANULARITY["year"] == "month"

    def test_month_and_week_map_to_day(self) -> None:
        assert TIME_TO_GRANULARITY["month"] == "day"
        assert TIME_TO_GRANULARITY["week"] == "day"

    def test_every_time_variant_has_granularity(self) -> None:
        for time_variant in TIME_VARIANTS:
            assert time_variant in TIME_TO_GRANULARITY


class TestClassifyCountryTheater:
    def test_iran_short_name_classified_as_core_me(self) -> None:
        assert classify_country_theater("Iran") == "core_me"

    def test_israel_classified_as_core_me(self) -> None:
        assert classify_country_theater("Israel") == "core_me"

    def test_turkey_classified_as_extended_me(self) -> None:
        assert classify_country_theater("Turkey") == "extended_me"

    def test_united_states_classified_as_global_terror(self) -> None:
        assert classify_country_theater("United States") == "global_terror"

    def test_unknown_country_falls_through_to_other(self) -> None:
        assert classify_country_theater("Burkina Faso") == "other"

    def test_syria_short_name_resolves(self) -> None:
        assert classify_country_theater("Syria") == "core_me"


class TestParseOverviewYearAll:
    @pytest.fixture()
    def rows(self) -> list[AggregateRow]:
        payload = _load(YEAR_ALL_FIXTURE)
        return parse_overview(payload, "year", "all")

    def test_produces_rows(self, rows: list[AggregateRow]) -> None:
        assert len(rows) > 0

    def test_all_rows_have_month_granularity(self, rows: list[AggregateRow]) -> None:
        assert all(r.granularity == "month" for r in rows)

    def test_all_rows_have_disorder_all(self, rows: list[AggregateRow]) -> None:
        assert all(r.disorder_type == "all" for r in rows)

    def test_source_file_is_stored(self, rows: list[AggregateRow]) -> None:
        assert all(r.source_file == "year_all_overview.json" for r in rows)

    def test_bucket_dates_are_date_instances(self, rows: list[AggregateRow]) -> None:
        assert all(isinstance(r.bucket_start_date, date) for r in rows)

    def test_latest_update_parsed(self, rows: list[AggregateRow]) -> None:
        assert all(isinstance(r.latest_update, date) for r in rows)

    def test_country_name_resolved_for_known_id(self, rows: list[AggregateRow]) -> None:
        by_id = {r.country_id: r for r in rows}
        assert 4 in by_id
        assert by_id[4].country_name == "Afghanistan"

    def test_theater_classified_for_known_country(self, rows: list[AggregateRow]) -> None:
        iran_rows = [r for r in rows if r.country_name == "Iran"]
        assert iran_rows
        assert all(r.theater == "core_me" for r in iran_rows)

    def test_nonnegative_counts(self, rows: list[AggregateRow]) -> None:
        assert all(r.events >= 0 and r.fatalities >= 0 and r.exposure >= 0 for r in rows)


class TestParseOverviewWeekAll:
    def test_week_all_uses_day_granularity(self) -> None:
        payload = _load(WEEK_ALL_FIXTURE)
        rows = parse_overview(payload, "week", "all")
        assert rows
        assert all(r.granularity == "day" for r in rows)


class TestParseOverviewMonthAll:
    def test_month_all_uses_day_granularity(self) -> None:
        payload = _load(MONTH_ALL_FIXTURE)
        rows = parse_overview(payload, "month", "all")
        assert rows
        assert all(r.granularity == "day" for r in rows)


class TestParseOverviewDisorderVariant:
    def test_year_politicalviolence_stores_disorder_type(self) -> None:
        payload = _load(YEAR_PV_FIXTURE)
        rows = parse_overview(payload, "year", "politicalviolence")
        assert rows
        assert all(r.disorder_type == "politicalviolence" for r in rows)
        assert all(r.source_file == "year_politicalviolence_overview.json" for r in rows)


class TestParseOverviewMalformed:
    def test_missing_country_timeline_returns_empty(self) -> None:
        rows = parse_overview({"latestUpdate": "2026-04-03"}, "year", "all")
        assert rows == []

    def test_row_missing_date_is_skipped(self) -> None:
        payload = {
            "latestUpdate": "2026-04-03",
            "countries": [{"id": 4, "name": "Afghanistan"}],
            "countryTimeline": [
                {"id": 4, "events": 10, "fatalities": 1},  # missing date
                {"date": "2025-05-01", "id": 4, "events": 20, "fatalities": 2, "exposure": 1000},
            ],
        }
        rows = parse_overview(payload, "year", "all")
        assert len(rows) == 1
        assert rows[0].events == 20

    def test_row_with_unknown_country_id_gets_placeholder_name(self) -> None:
        payload = {
            "latestUpdate": "2026-04-03",
            "countries": [],
            "countryTimeline": [
                {"date": "2025-05-01", "id": 999, "events": 5, "fatalities": 0, "exposure": 0},
            ],
        }
        rows = parse_overview(payload, "year", "all")
        assert len(rows) == 1
        assert rows[0].country_name == "id-999"

    def test_invalid_latest_update_falls_back_to_today(self) -> None:
        payload = {
            "latestUpdate": "not-a-date",
            "countries": [{"id": 4, "name": "Afghanistan"}],
            "countryTimeline": [
                {"date": "2025-05-01", "id": 4, "events": 1, "fatalities": 0, "exposure": 0},
            ],
        }
        rows = parse_overview(payload, "year", "all")
        assert len(rows) == 1
        # Fallback: must still be a date, not None
        assert isinstance(rows[0].latest_update, date)


class TestUpsertAggregates:
    def test_empty_list_is_noop(self, db: Session) -> None:
        inserted = upsert_aggregates(db, [])
        assert inserted == 0
        assert db.scalar(select(func.count()).select_from(AcledAggregate)) == 0

    def test_upsert_stores_rows(self, db: Session) -> None:
        rows = parse_overview(_load(YEAR_ALL_FIXTURE), "year", "all")
        upsert_aggregates(db, rows)
        stored = db.scalar(select(func.count()).select_from(AcledAggregate))
        assert stored == len(rows)

    def test_reingest_is_idempotent(self, db: Session) -> None:
        rows = parse_overview(_load(YEAR_ALL_FIXTURE), "year", "all")
        upsert_aggregates(db, rows)
        first_count = db.scalar(select(func.count()).select_from(AcledAggregate))
        upsert_aggregates(db, rows)
        second_count = db.scalar(select(func.count()).select_from(AcledAggregate))
        assert first_count == second_count

    def test_different_disorder_variants_coexist(self, db: Session) -> None:
        all_rows = parse_overview(_load(YEAR_ALL_FIXTURE), "year", "all")
        pv_rows = parse_overview(_load(YEAR_PV_FIXTURE), "year", "politicalviolence")
        upsert_aggregates(db, all_rows)
        upsert_aggregates(db, pv_rows)
        total = db.scalar(select(func.count()).select_from(AcledAggregate))
        assert total == len(all_rows) + len(pv_rows)

    def test_all_disorder_variants_defined(self) -> None:
        assert "all" in DISORDER_VARIANTS
        assert "politicalviolence" in DISORDER_VARIANTS
        assert "terroristactivity" in DISORDER_VARIANTS
        assert len(DISORDER_VARIANTS) == 8
