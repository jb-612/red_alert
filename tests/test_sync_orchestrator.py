"""Tests for the cross-source sync orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from backend.sync.orchestrator import (
    SourceResult,
    SourceSpec,
    SyncRegistry,
    run_sources,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture()
def fake_db() -> Session:
    return MagicMock(name="Session")


def _ok_source(name: str, rows: int) -> SourceSpec:
    def _fn(_db: Session) -> int:
        return rows

    return SourceSpec(name=name, sync=_fn, label=name.title(), slow=False)


def _failing_source(name: str, exc: Exception) -> SourceSpec:
    def _fn(_db: Session) -> int:
        raise exc

    return SourceSpec(name=name, sync=_fn, label=name.title(), slow=False)


class TestRunSourcesHappyPath:
    def test_runs_all_sources_in_order(self, fake_db: Session) -> None:
        results = run_sources(
            fake_db,
            [_ok_source("alpha", 5), _ok_source("beta", 10)],
        )
        assert [r.source for r in results] == ["alpha", "beta"]
        assert all(r.status == "ok" for r in results)

    def test_returns_row_counts(self, fake_db: Session) -> None:
        results = run_sources(fake_db, [_ok_source("alpha", 42)])
        assert results[0].rows_synced == 42
        assert results[0].error is None

    def test_captures_elapsed_time(self, fake_db: Session) -> None:
        results = run_sources(fake_db, [_ok_source("alpha", 1)])
        assert results[0].elapsed_seconds >= 0

    def test_empty_source_list_returns_empty_results(self, fake_db: Session) -> None:
        assert run_sources(fake_db, []) == []


class TestRunSourcesFailureIsolation:
    def test_one_failing_source_does_not_stop_others(self, fake_db: Session) -> None:
        results = run_sources(
            fake_db,
            [
                _ok_source("alpha", 1),
                _failing_source("beta", ValueError("boom")),
                _ok_source("gamma", 3),
            ],
        )
        assert [r.source for r in results] == ["alpha", "beta", "gamma"]
        assert results[0].status == "ok"
        assert results[1].status == "error"
        assert "boom" in (results[1].error or "")
        assert results[2].status == "ok"

    def test_failing_source_has_zero_rows(self, fake_db: Session) -> None:
        results = run_sources(
            fake_db, [_failing_source("beta", RuntimeError("nope"))]
        )
        assert results[0].rows_synced == 0

    def test_exception_type_is_recorded(self, fake_db: Session) -> None:
        results = run_sources(
            fake_db, [_failing_source("beta", ValueError("bad"))]
        )
        error = results[0].error or ""
        assert "ValueError" in error or "bad" in error


class TestSourceResultModel:
    def test_source_result_fields(self) -> None:
        r = SourceResult(
            source="alpha",
            label="Alpha",
            status="ok",
            rows_synced=7,
            elapsed_seconds=1.25,
            error=None,
        )
        assert r.source == "alpha"
        assert r.status == "ok"
        assert r.rows_synced == 7


class TestSyncRegistry:
    def test_registry_has_expected_sources(self) -> None:
        registry = SyncRegistry.default()
        names = {s.name for s in registry.all()}
        assert "tzofar" in names
        assert "oref" in names
        assert "acled_aggregates" in names

    def test_registry_get_by_name(self) -> None:
        registry = SyncRegistry.default()
        spec = registry.get("tzofar")
        assert spec is not None
        assert spec.name == "tzofar"

    def test_registry_get_unknown_returns_none(self) -> None:
        registry = SyncRegistry.default()
        assert registry.get("nonexistent") is None

    def test_registry_select_default_filters_to_fast_sources(self) -> None:
        registry = SyncRegistry.default()
        fast = registry.select_default()
        assert all(not s.slow for s in fast)
        assert len(fast) >= 3

    def test_registry_select_by_names_preserves_order(self) -> None:
        registry = SyncRegistry.default()
        selected = registry.select(["oref", "tzofar"])
        assert [s.name for s in selected] == ["oref", "tzofar"]

    def test_registry_select_skips_unknown_names(self) -> None:
        registry = SyncRegistry.default()
        selected = registry.select(["oref", "unknown_source"])
        assert [s.name for s in selected] == ["oref"]
