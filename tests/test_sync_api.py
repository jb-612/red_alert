"""Tests for the POST /api/sync endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.sync.orchestrator import SourceSpec, SyncRegistry

if TYPE_CHECKING:
    from collections.abc import Iterator


def _fake_registry(rows_by_source: dict[str, int]) -> SyncRegistry:
    """Build a registry whose every sync just returns a fixed row count."""
    def make_sync(rows: int):
        def _fn(_db) -> int:
            return rows

        return _fn

    return SyncRegistry(
        sources=[
            SourceSpec(name=name, sync=make_sync(rows), label=name.title(), slow=False)
            for name, rows in rows_by_source.items()
        ]
    )


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


class TestRefreshEndpoint:
    def test_default_runs_all_fast_sources(self, client: TestClient) -> None:
        fake = _fake_registry({"tzofar": 5, "oref": 10, "acled_aggregates": 42})
        with patch("backend.api.sync.SyncRegistry.default", return_value=fake):
            resp = client.post("/api/sync")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok_count"] == 3
        assert body["error_count"] == 0
        assert body["total_rows"] == 57

    def test_selecting_specific_sources(self, client: TestClient) -> None:
        fake = _fake_registry({"tzofar": 5, "oref": 10, "acled_aggregates": 42})
        with patch("backend.api.sync.SyncRegistry.default", return_value=fake):
            resp = client.post("/api/sync", json={"sources": ["oref"]})
        body = resp.json()
        assert body["ok_count"] == 1
        assert body["results"][0]["source"] == "oref"
        assert body["results"][0]["rows_synced"] == 10

    def test_failing_source_reported_in_results(self, client: TestClient) -> None:
        def bad_sync(_db) -> int:
            raise RuntimeError("upstream down")

        def good_sync(_db) -> int:
            return 3

        fake = SyncRegistry(
            sources=[
                SourceSpec(name="ok", sync=good_sync, label="Ok", slow=False),
                SourceSpec(name="bad", sync=bad_sync, label="Bad", slow=False),
            ]
        )
        with patch("backend.api.sync.SyncRegistry.default", return_value=fake):
            resp = client.post("/api/sync")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok_count"] == 1
        assert body["error_count"] == 1
        bad_result = next(r for r in body["results"] if r["source"] == "bad")
        assert bad_result["status"] == "error"
        assert "upstream down" in bad_result["error"]

    def test_unknown_source_names_are_skipped(self, client: TestClient) -> None:
        fake = _fake_registry({"tzofar": 5})
        with patch("backend.api.sync.SyncRegistry.default", return_value=fake):
            resp = client.post("/api/sync", json={"sources": ["tzofar", "nonexistent"]})
        body = resp.json()
        assert len(body["results"]) == 1
        assert body["results"][0]["source"] == "tzofar"


class TestListSourcesEndpoint:
    def test_lists_registered_sources(self, client: TestClient) -> None:
        resp = client.get("/api/sync/sources")
        assert resp.status_code == 200
        names = {row["name"] for row in resp.json()}
        assert {"tzofar", "oref", "acled_aggregates", "acled_events"} <= names

    def test_sources_have_slow_flag(self, client: TestClient) -> None:
        resp = client.get("/api/sync/sources")
        by_name = {row["name"]: row for row in resp.json()}
        assert by_name["acled_events"]["slow"] is True
        assert by_name["tzofar"]["slow"] is False
