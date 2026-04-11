"""Pydantic schemas for the cross-source sync refresh endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SyncSourceResult(BaseModel):
    """Per-source outcome of a sync run."""

    source: str = Field(description="Source identifier key")
    label: str = Field(description="Human-readable source name")
    status: str = Field(description="'ok' or 'error'")
    rows_synced: int = Field(description="Rows inserted or upserted")
    elapsed_seconds: float = Field(description="Wall-clock time the source took")
    error: str | None = Field(default=None, description="Error message if status == 'error'")


class SyncResponse(BaseModel):
    """Aggregate response for a refresh-all request."""

    results: list[SyncSourceResult]
    total_rows: int = Field(description="Sum of rows across all sources")
    total_elapsed_seconds: float = Field(description="Wall-clock time across all sources")
    ok_count: int = Field(description="Number of sources that succeeded")
    error_count: int = Field(description="Number of sources that failed")


class SyncRequest(BaseModel):
    """Optional request body for selecting a subset of sources."""

    sources: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of source names to sync. "
            "If omitted, the default fast set is used."
        ),
    )
