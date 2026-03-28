# Coding Standards — Red Alert Analytics Dashboard

## Data Integrity Rules

1. **BOM stripping** — All OREF API response handling must strip UTF-8 BOM before JSON parsing. Use `codecs.decode(text.encode(), 'utf-8-sig')` in Python or `.replace(/^\uFEFF/, '')` in JavaScript.
2. **Deduplication** — Never insert duplicate alerts. Deduplicate by `(alert_datetime, location_name, category)` tuple. The `source` field tracks provenance.
3. **Hebrew text preservation** — Always store original Hebrew text. Never discard, transliterate, or replace with English-only. Store translations in `_en` suffixed fields.
4. **Timezone handling** — Store all timestamps as `TIMESTAMPTZ` (UTC). OREF uses `DD.MM.YYYY` in queries. Display in `Asia/Jerusalem` timezone.

## Python Backend (`backend/`)

5. Python 3.11+ with full type annotations on all function signatures.
6. Use `uv` for dependency management.
7. `ruff` for linting and formatting (auto-enforced by PostToolUse hook).
8. Cyclomatic complexity cap: CC <= 5 per function (enforced by PostToolUse hook).
9. Import order: stdlib, third-party, local modules.
10. Pydantic models with `Field(description=...)` for all API request/response schemas.
11. SQLAlchemy models for database tables.
12. f-strings for string formatting.
13. Specific exceptions — no bare `except:` or `except Exception`.
14. All FastAPI endpoints include docstrings (generates OpenAPI docs).

## Frontend (`frontend/`)

15. Functional React components with TypeScript.
16. No `any` type — use proper TypeScript types.

## Configuration

17. Environment variables prefixed with `RED_ALERT_` (never hardcode URLs, API keys, or database credentials).
18. Downloaded data files (CSVs, large JSONs) go in `data/` (gitignored).
