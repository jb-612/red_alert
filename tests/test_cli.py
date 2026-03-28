"""Tests for backend.cli module."""

from unittest.mock import patch

import pytest

from backend.cli import build_parser, seed_categories
from backend.models.category import AlertCategory


def test_build_parser_backfill():
    parser = build_parser()
    args = parser.parse_args(["backfill"])
    assert args.command == "backfill"


def test_build_parser_seed_categories():
    parser = build_parser()
    args = parser.parse_args(["seed-categories"])
    assert args.command == "seed-categories"


def test_build_parser_serve():
    parser = build_parser()
    args = parser.parse_args(["serve"])
    assert args.command == "serve"


def test_build_parser_serve_custom_port():
    parser = build_parser()
    args = parser.parse_args(["serve", "--port", "9000"])
    assert args.command == "serve"
    assert args.port == 9000


def test_build_parser_no_command():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command is None


def test_seed_categories(db):
    count = seed_categories(db)
    assert count == 9
    cats = db.query(AlertCategory).all()
    assert len(cats) == 9
    # Check a specific one
    cat1 = db.query(AlertCategory).filter_by(id=1).first()
    assert cat1.name_en == "Rocket and missile fire"
    assert cat1.name_he == "ירי רקטות וטילים"


def test_seed_categories_idempotent(db):
    """Seeding twice should not fail or create duplicates."""
    first = seed_categories(db)
    second = seed_categories(db)
    assert first == 9
    assert second == 0
    assert db.query(AlertCategory).count() == 9
