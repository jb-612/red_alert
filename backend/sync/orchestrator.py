"""Cross-source sync orchestrator.

A `SourceSpec` wraps one data source with a uniform `(Session) -> int` sync
callable. `run_sources` iterates a list of specs, calling each one, timing it,
and catching exceptions into a structured `SourceResult` so a single failing
source never breaks the rest of the refresh.

`SyncRegistry.default()` returns the project's canonical list of sources:
Tzofar, OREF, ACLED aggregates, and ACLED events. The ACLED events source is
marked `slow=True` because it paginates through potentially thousands of
rows; callers can exclude slow sources by default via `select_default()`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from backend.ingestion.acled_aggregate_client import sync_all_aggregates
from backend.ingestion.acled_client import ingest_acled_events
from backend.ingestion.oref_client import ingest_oref_history
from backend.ingestion.tzofar_client import ingest_tzofar_alerts

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

SyncCallable = Callable[["Session"], int]


@dataclass(frozen=True)
class SourceSpec:
    """One data source that can be refreshed."""

    name: str
    sync: SyncCallable
    label: str
    slow: bool = False


@dataclass(frozen=True)
class SourceResult:
    """Outcome of running a single source's sync."""

    source: str
    label: str
    status: str  # "ok" | "error"
    rows_synced: int
    elapsed_seconds: float
    error: str | None = None


def _format_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _run_one(db: Session, spec: SourceSpec) -> SourceResult:
    """Run a single source, capturing exceptions into a structured result."""
    start = time.monotonic()
    try:
        rows = int(spec.sync(db))
    except Exception as exc:
        elapsed = time.monotonic() - start
        logger.warning("Sync source %s failed: %s", spec.name, exc)
        return SourceResult(
            source=spec.name,
            label=spec.label,
            status="error",
            rows_synced=0,
            elapsed_seconds=round(elapsed, 2),
            error=_format_error(exc),
        )
    elapsed = time.monotonic() - start
    logger.info("Sync source %s ok: %d rows in %.2fs", spec.name, rows, elapsed)
    return SourceResult(
        source=spec.name,
        label=spec.label,
        status="ok",
        rows_synced=rows,
        elapsed_seconds=round(elapsed, 2),
        error=None,
    )


def run_sources(db: Session, specs: Iterable[SourceSpec]) -> list[SourceResult]:
    """Run each source in order, capturing per-source results.

    Failures in one source do not stop the others. Each result records
    status ("ok" | "error"), rows synced, and elapsed seconds.
    """
    return [_run_one(db, spec) for spec in specs]


@dataclass
class SyncRegistry:
    """Lookup + selection logic for the project's data sources."""

    sources: list[SourceSpec] = field(default_factory=list)

    @classmethod
    def default(cls) -> SyncRegistry:
        """The canonical list of sources wired to the real ingestion clients."""

        return cls(
            sources=[
                SourceSpec(
                    name="tzofar",
                    sync=ingest_tzofar_alerts,
                    label="Tzofar alerts",
                    slow=False,
                ),
                SourceSpec(
                    name="oref",
                    sync=ingest_oref_history,
                    label="OREF history",
                    slow=False,
                ),
                SourceSpec(
                    name="acled_aggregates",
                    sync=sync_all_aggregates,
                    label="ACLED aggregates",
                    slow=False,
                ),
                SourceSpec(
                    name="acled_events",
                    sync=ingest_acled_events,
                    label="ACLED events",
                    slow=True,
                ),
            ]
        )

    def all(self) -> list[SourceSpec]:
        return list(self.sources)

    def get(self, name: str) -> SourceSpec | None:
        for spec in self.sources:
            if spec.name == name:
                return spec
        return None

    def select(self, names: list[str]) -> list[SourceSpec]:
        """Resolve a list of source names to specs, preserving order and skipping unknowns."""
        resolved: list[SourceSpec] = []
        for name in names:
            spec = self.get(name)
            if spec is not None:
                resolved.append(spec)
        return resolved

    def select_default(self) -> list[SourceSpec]:
        """The default set used by the refresh button — fast sources only."""
        return [spec for spec in self.sources if not spec.slow]
