"""Dialect-aware SQL expression builders.

Abstracts SQLite-specific SQL (func.strftime) into reusable functions.
When migrating to PostgreSQL, only this module needs to change.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.sql.expression import Function


def extract_date(col: Any) -> Function[Any]:
    """Extract date as string YYYY-MM-DD."""
    return func.strftime("%Y-%m-%d", col)


def extract_hour(col: Any) -> Function[Any]:
    """Extract hour as two-digit string HH."""
    return func.strftime("%H", col)


def extract_dow(col: Any) -> Function[Any]:
    """Extract day of week as string (0=Sunday, SQLite %w convention)."""
    return func.strftime("%w", col)


def extract_week(col: Any) -> Function[Any]:
    """Extract ISO week as string YYYY-WNN."""
    return func.strftime("%Y-W%W", col)


def extract_month(col: Any) -> Function[Any]:
    """Extract month as string YYYY-MM."""
    return func.strftime("%Y-%m", col)
