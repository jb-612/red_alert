"""HTTP endpoint to refresh data from all (or selected) upstream sources."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.sync import SyncRequest, SyncResponse, SyncSourceResult
from backend.sync.orchestrator import (
    SourceResult,
    SourceSpec,
    SyncRegistry,
    run_sources,
)

router = APIRouter(prefix="/api/sync", tags=["sync"])


def _result_to_schema(result: SourceResult) -> SyncSourceResult:
    return SyncSourceResult(
        source=result.source,
        label=result.label,
        status=result.status,
        rows_synced=result.rows_synced,
        elapsed_seconds=result.elapsed_seconds,
        error=result.error,
    )


def _resolve_sources(registry: SyncRegistry, request: SyncRequest | None) -> list[SourceSpec]:
    if request and request.sources:
        return registry.select(request.sources)
    return registry.select_default()


@dataclass
class _SyncTotals:
    rows: int = 0
    elapsed: float = 0.0
    ok: int = 0
    errors: int = 0


def _accumulate_totals(results: list[SourceResult]) -> _SyncTotals:
    totals = _SyncTotals()
    for r in results:
        totals.rows += r.rows_synced
        totals.elapsed += r.elapsed_seconds
        if r.status == "ok":
            totals.ok += 1
        else:
            totals.errors += 1
    return totals


def _build_response(results: list[SourceResult]) -> SyncResponse:
    items = [_result_to_schema(r) for r in results]
    totals = _accumulate_totals(results)
    return SyncResponse(
        results=items,
        total_rows=totals.rows,
        total_elapsed_seconds=round(totals.elapsed, 2),
        ok_count=totals.ok,
        error_count=totals.errors,
    )


@router.post("", response_model=SyncResponse)
def refresh_all(
    request: SyncRequest | None = None,
    db: Session = Depends(get_db),
) -> SyncResponse:
    """Refresh data from upstream sources.

    With no request body, runs the default set of fast sources
    (Tzofar, OREF, ACLED aggregates). Pass `{"sources": [...]}` to pick a
    specific subset — valid names include `tzofar`, `oref`,
    `acled_aggregates`, and `acled_events`.

    Each source runs in isolation: one failure does not stop the others.
    The response reports per-source status, rows synced, and elapsed time.
    """
    registry = SyncRegistry.default()
    specs = _resolve_sources(registry, request)
    results = run_sources(db, specs)
    return _build_response(results)


@router.get("/sources", response_model=list[dict])
def list_sources() -> list[dict]:
    """List every source the refresh endpoint knows about."""
    registry = SyncRegistry.default()
    return [
        {"name": s.name, "label": s.label, "slow": s.slow}
        for s in registry.all()
    ]
