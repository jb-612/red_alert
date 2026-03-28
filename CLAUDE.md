# Red Alert Analytics Dashboard

Analytics dashboard for Israel's Home Front Command (OREF) alert history data from https://www.oref.org.il/heb/alerts-history.
Tech stack: Python (FastAPI) backend, React frontend, PostgreSQL/TimescaleDB.

## Build/Test Commands

### Backend (Python)
- Create virtual environment: `uv venv`
- Install with dev deps: `uv pip install -e ".[dev]"`
- Run all tests: `uv run pytest tests/ -v`
- Run tests with coverage: `uv run pytest tests/ -v --cov=backend --cov-report=term-missing`
- Run a single test: `uv run pytest tests/test_ingestion.py::test_bom_stripping -v`
- Run linter: `uv run ruff check backend/` (25 rule sets)
- Run formatter: `uv run ruff format backend/`
- Type checking: `uv run mypy backend/`
- Dead code: `uv run vulture backend/ --min-confidence 80`
- Cyclomatic complexity: `uv run radon cc -s -n C backend/`
- Cognitive complexity: `uv run complexipy backend/ --max-complexity 15 --quiet`
- Maintainability index: `uv run radon mi -s -n B backend/`
- **Run all 8 quality gates**: `.claude/hooks/quality-gate.sh`

### Frontend (React/TypeScript)
- Install: `npm install`
- Dev server: `npm run dev`
- Tests: `npm test`
- Lint: `npm run lint`

### Infrastructure
- Database: `docker compose up -d db`
- Full stack: `docker compose up`

## Project Architecture

```
red_alert/
├── backend/              # FastAPI application
│   ├── api/              # REST endpoints
│   ├── ingestion/        # Data pipeline (Tzofar, OREF, CSV)
│   ├── models/           # SQLAlchemy + Pydantic models
│   └── analytics/        # Aggregation and query logic
├── frontend/             # React dashboard
│   ├── components/       # Charts, maps, filters
│   └── api/              # API client
├── tests/                # pytest test suite
├── data/                 # Downloaded datasets (gitignored)
├── docs/                 # Research and design documents
│   ├── design/           # Architecture and design docs
│   └── research/         # API research, repo reviews
└── docker/               # Docker and compose files
```

### Core Database Tables
- `alerts` — alert_datetime, location_name, category, lat/lng, source, raw_data
- `locations` — name (he/en/ru/ar), zone, coordinates, countdown_sec, shelter_count
- `alert_categories` — id, name_he, name_en

See `docs/design/architecture.md` for full schema and data flow diagrams.

## Key API Endpoints and Data Sources

| Source | URL | Geo-Blocked | Use Case |
|--------|-----|-------------|----------|
| OREF Real-time | `https://www.oref.org.il/WarningMessages/alert/alerts.json` | Yes | Live alerts (poll every 2-3s) |
| OREF History 24h | `https://www.oref.org.il/WarningMessages/History/AlertsHistory.json` | Yes | Recent history |
| OREF Date Range | `https://www.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate=DD.MM.YYYY&toDate=DD.MM.YYYY&mode=0` | Yes | Historical queries |
| Tzofar REST | `https://api.tzevaadom.co.il/alerts-history` | **No** | Primary ingestion |
| Tzofar WebSocket | `wss://ws.tzevaadom.co.il/socket?platform=ANDROID` | **No** | Real-time push |
| CSV Backfill | `github.com/dleshem/israel-alerts-data` | No | Historical backfill |

### Required OREF Headers
```
Referer: https://www.oref.org.il/
X-Requested-With: XMLHttpRequest
User-Agent: <browser UA string>
```

### UTF-8 BOM Caveat
All OREF API responses include a UTF-8 BOM (`EF BB BF`). Must strip before JSON parsing:
```python
import codecs
clean = codecs.decode(response.text.encode(), 'utf-8-sig')
data = json.loads(clean)
```

## Key Conventions

- **Naming:** `snake_case` for Python, `camelCase` for JS/TS, `PascalCase` for React components and Python classes
- **Hebrew text:** Always store original Hebrew. English translations in `_en` suffixed columns/fields
- **Deduplication:** By `(alert_datetime, location_name, category)` tuple. `source` field tracks provenance
- **Dates:** Store as `TIMESTAMPTZ` (UTC). OREF queries use `DD.MM.YYYY`. Display in `Asia/Jerusalem`
- **Config:** Environment variables prefixed with `RED_ALERT_` — never hardcode URLs, API keys, or DB credentials
- **Data files:** Downloaded CSVs and large JSONs go in `data/` (gitignored)

## Code Style Guidelines

- Python 3.11+ with full type annotations (enforced by `ANN` rules + `mypy`)
- `uv` for dependency management
- `ruff` for linting and formatting — 25 rule sets (auto-enforced by PostToolUse hook)
- `mypy` for static type checking (auto-enforced by PostToolUse hook)
- Cyclomatic complexity: CC <= 5 per function (enforced by `C90` rule + radon hook)
- Cognitive complexity: <= 15 per function (checked by `complexipy`)
- Maintainability index: >= grade B per file (checked by `radon mi`)
- Test coverage: >= 60% (enforced by `pytest-cov`, target 80%)
- Import order: stdlib, third-party, local modules
- Pydantic models with `Field(description=...)` for API request/response schemas
- SQLAlchemy models for database tables
- f-strings for formatting, specific exceptions (no bare `except:`)
- All FastAPI endpoints include docstrings (generates OpenAPI docs)
- Frontend: functional React components, TypeScript only, no `any` type

## Development Workflow

1. **Plan before code** — discuss approach before implementing a feature
2. **Tests first** — write tests before implementation for all backend logic
3. **Check complexity** — report when cyclomatic complexity exceeds 5
4. **Lint before commit** — `ruff check` and `ruff format` before committing
5. **Never force push** — no `git push --force` without explicit permission
6. **Never push without asking** — always confirm before pushing to remote
7. **Conventional commits** — `type(scope): description` (feat, fix, refactor, test, chore, docs)
8. **Document API quirks** — new API behavior goes into `docs/research/`

## Non-Negotiable Rules

1. **Never commit secrets** — no API keys, database passwords, or `.env` files in git
2. **Strip BOM before parsing** — all OREF response handling must strip UTF-8 BOM
3. **Deduplicate on ingest** — never insert duplicate alerts; check `(datetime, location, category)`
4. **Hebrew text preserved** — never discard or transliterate original Hebrew; always store source text
5. **Graceful degradation** — ingestion must work with Tzofar alone (OREF may be unavailable)
6. **Protected files require confirmation** — `CLAUDE.md`, `.claude/**`, DB migrations, Docker config

## Specialized Agents

| Agent | Role | Constraints |
|-------|------|-------------|
| `reviewer` | Read-only code review | Cannot modify files. Checks data integrity, API correctness, security, code quality |
| `test-writer` | TDD RED phase — writes failing tests | Can only edit `tests/`, not `backend/` or `frontend/` |

## Available Skills

| Skill | Description |
|-------|-------------|
| `/commit` | Conventional commit with scope and pre-commit validation |
| `/testing` | Run 8 quality gates: tests+coverage, ruff (25 rules), formatting, mypy, vulture, CC, cognitive, MI |
| `/code-review` | Two-phase review: automated quality gates then manual (data integrity, API, security, types) |
| `/data-explore` | Explore and validate data sources (Tzofar, OREF, CSV) |

## Quality Gate Metrics (SonarQube-Equivalent)

| Metric | Tool | Threshold |
|--------|------|-----------|
| Bugs | Ruff B + PL + mypy | 0 |
| Vulnerabilities | Ruff S (bandit rules) | 0 |
| Code Smells | Ruff SIM, C4, RET, PERF, ERA, PTH | 0 |
| Test Coverage | pytest-cov | >= 60% (target 80%) |
| Dead Code | vulture | 0 at 80% confidence |
| Cyclomatic Complexity | Ruff C90 + radon | CC <= 5 |
| Cognitive Complexity | complexipy | <= 15 |
| Maintainability Index | radon MI | >= grade B |
| Type Safety | mypy + Ruff ANN | 0 errors |
| Timezone Safety | Ruff DTZ | 0 |
| Security | Ruff S (47 bandit rules) | 0 |
