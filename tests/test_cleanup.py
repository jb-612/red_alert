"""Tests for Batch 5 cleanup items.

WI-5.2: MostActiveCategory.name should be the Hebrew category_desc
WI-5.3: Dead code removal (bulk_insert_deduped, load_csv_from_url)
WI-5.4: Inline imports moved to top of cli.py
"""

import ast
import importlib
from datetime import datetime

import pytest

from backend.models.alert import Alert
from backend.models.category import AlertCategory
from backend.models.location import Location


def test_cli_no_inline_imports_in_cmd_backfill():
    """WI-5.4: httpx, sys, sqlalchemy func/select, and Alert should be imported at module top."""

    source = importlib.util.find_spec("backend.cli")
    assert source is not None
    assert source.origin is not None

    with open(source.origin) as f:
        tree = ast.parse(f.read())

    # Collect top-level import names
    top_level_imports: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level_imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_level_imports.add(node.module)

    # These should be at the top level, not inside functions
    assert "httpx" in top_level_imports, "httpx should be a top-level import in cli.py"
    assert "backend.models.alert" in top_level_imports, (
        "backend.models.alert should be a top-level import in cli.py"
    )


def test_bulk_insert_deduped_removed():
    """WI-5.3: bulk_insert_deduped should be removed from deduplication module."""
    from backend.ingestion import deduplication

    assert not hasattr(deduplication, "bulk_insert_deduped"), (
        "bulk_insert_deduped should be removed (dead code)"
    )


def test_load_csv_from_url_removed():
    """WI-5.3: load_csv_from_url should be removed from csv_loader module."""
    from backend.ingestion import csv_loader

    assert not hasattr(csv_loader, "load_csv_from_url"), (
        "load_csv_from_url should be removed (dead code)"
    )


@pytest.fixture
def _seed_kpi_data(db_session):
    """Seed minimal data for KPI test."""
    db_session.add(Alert(
        alert_datetime=datetime(2024, 1, 1, 10, 0),
        location_name="תל אביב",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ))
    db_session.add(Alert(
        alert_datetime=datetime(2024, 1, 1, 10, 5),
        location_name="חיפה",
        category=1,
        category_desc="ירי רקטות וטילים",
        source="test",
    ))
    db_session.commit()
    yield
    db_session.query(Alert).delete()
    db_session.query(Location).delete()
    db_session.query(AlertCategory).delete()
    db_session.commit()


def test_most_active_category_name_is_hebrew(_seed_kpi_data, client):
    """WI-5.2: MostActiveCategory.name should contain the Hebrew category_desc."""
    response = client.get("/api/analytics/kpi")
    data = response.json()

    mac = data["most_active_category"]
    # name should be Hebrew
    assert mac["name"] == "ירי רקטות וטילים"
    # name_en should be empty or different (not duplicated Hebrew)
    assert mac["name_en"] == ""
