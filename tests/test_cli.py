"""Tests for backend.cli module."""

from unittest.mock import patch

import httpx
import pytest

from backend.cli import build_parser, cmd_backfill, seed_categories
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
    assert cat1.name_he == "\u05d9\u05e8\u05d9 \u05e8\u05e7\u05d8\u05d5\u05ea \u05d5\u05d8\u05d9\u05dc\u05d9\u05dd"


def test_seed_categories_idempotent(db):
    """Seeding twice should not fail or create duplicates."""
    first = seed_categories(db)
    second = seed_categories(db)
    assert first == 9
    assert second == 0
    assert db.query(AlertCategory).count() == 9


# --- WI-2.1: HTTP error handling tests ---


def test_backfill_download_failure_http_error() -> None:
    """cmd_backfill exits with code 1 when HTTP status error occurs during download."""
    mock_response = httpx.Response(status_code=500, request=httpx.Request("GET", "http://test"))
    with (
        patch("backend.cli.init_db"),
        patch("backend.cli.SessionLocal"),
        patch("httpx.Client") as mock_cls,
    ):
        mock_instance = mock_cls.return_value.__enter__.return_value
        mock_instance.get.side_effect = httpx.HTTPStatusError(
            "Server error", request=httpx.Request("GET", "http://test"), response=mock_response
        )
        with pytest.raises(SystemExit, match="1"):
            cmd_backfill()


def test_backfill_download_failure_connect_error() -> None:
    """cmd_backfill exits with code 1 when connection fails during download."""
    with (
        patch("backend.cli.init_db"),
        patch("backend.cli.SessionLocal"),
        patch("httpx.Client") as mock_cls,
    ):
        mock_instance = mock_cls.return_value.__enter__.return_value
        mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
        with pytest.raises(SystemExit, match="1"):
            cmd_backfill()


def test_backfill_download_failure_timeout() -> None:
    """cmd_backfill exits with code 1 when download times out."""
    with (
        patch("backend.cli.init_db"),
        patch("backend.cli.SessionLocal"),
        patch("httpx.Client") as mock_cls,
    ):
        mock_instance = mock_cls.return_value.__enter__.return_value
        mock_instance.get.side_effect = httpx.TimeoutException("Timed out")
        with pytest.raises(SystemExit, match="1"):
            cmd_backfill()
