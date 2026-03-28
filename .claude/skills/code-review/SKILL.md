---
name: code-review
description: "Two-phase code review: automated quality gates then manual inspection for data integrity, API correctness, security, and types."
argument-hint: "[file, directory, or feature name]"
allowed-tools: Read, Glob, Grep, Bash
---

Review code for $ARGUMENTS using a two-phase approach:

## Phase 1: Automated Quality Gates

Run all automated checks first. Report results before proceeding to manual review.

### 1a. Expanded Linting (ruff — 25 rule sets)

```bash
uv run ruff check backend/ --output-format=grouped
```

Covers: security (S/bandit), bugs (B), complexity (C90), naming (N),
type annotations (ANN), timezone safety (DTZ), performance (PERF),
dead code (ERA), print detection (T20), and more.

### 1b. Type Checking (mypy)

```bash
uv run mypy backend/ --no-error-summary
```

Catches type errors that ruff cannot: wrong argument types,
incompatible return types, missing attributes, None-safety.

### 1c. Dead Code Detection (vulture)

```bash
uv run vulture backend/ --min-confidence 80
```

Finds unused functions, variables, imports, and unreachable code.

### 1d. Cognitive Complexity (complexipy)

```bash
uv run complexipy backend/ --max-complexity-allowed 15 --quiet
```

Cognitive complexity (how hard code is to *understand*) differs from
cyclomatic complexity (how many test paths exist). Threshold: 15.

### 1e. Cyclomatic Complexity (radon)

```bash
uv run radon cc -s -n C backend/
```

No functions above CC grade C (complexity > 5).

### 1f. Maintainability Index (radon)

```bash
uv run radon mi -s -n B backend/
```

No files below MI grade B (maintainability index < 20).

## Phase 2: Manual Review

After automated gates, review code for domain-specific issues that
tools cannot catch:

### 2a. Data Integrity
- OREF responses: BOM stripped before JSON parsing (`codecs.decode(text.encode(), 'utf-8-sig')`)
- Deduplication: `(datetime, location_name, category)` checked before insert
- Hebrew text: original preserved alongside translations in `_en` fields
- Timestamps: TIMESTAMPTZ in UTC, displayed in Asia/Jerusalem
- Coordinate bounds: lat 29-34, lng 34-36 (Israel)

### 2b. API Correctness
- Required OREF headers (Referer, X-Requested-With, User-Agent)
- Graceful degradation when OREF API unreachable (geo-blocking)
- Tzofar as primary source, OREF as secondary
- Error responses include meaningful messages
- All endpoints have docstrings (OpenAPI generation)

### 2c. Security
- Parameterized SQL queries only (no string concatenation/f-strings in queries)
- No hardcoded secrets or API keys (must use RED_ALERT_ env vars)
- Input validation on all API endpoints via Pydantic/Query validators
- No `eval()`, `exec()`, or `pickle.loads()` on external data
- CORS origins explicitly listed (not wildcard in production)

### 2d. Code Quality
- Type annotations on all function signatures (enforced by ANN rules)
- CC <= 5 per function (enforced by C90 rule)
- Pydantic models with `Field(description=...)` for API schemas
- SQLAlchemy models for database tables (no raw DDL)
- No bare `except:` — catch specific exceptions
- No mutable default arguments

## Output Format

```
## Review: [target]

### Phase 1: Automated Gates
| Gate                | Status | Details           |
|---------------------|--------|-------------------|
| Ruff (25 rule sets) | PASS/FAIL | N issues (N fixable) |
| Mypy                | PASS/FAIL | N type errors     |
| Vulture             | PASS/FAIL | N dead code items |
| Cognitive Complexity| PASS/FAIL | N functions > 15  |
| Cyclomatic Complexity| PASS/FAIL | N functions > CC5 |
| Maintainability     | PASS/FAIL | N files below B   |

### Phase 2: Manual Findings
1. [CRITICAL/WARNING/SUGGESTION] Description — file:line

### Verdict
PASS / NEEDS_CHANGES — N critical, N warnings, N suggestions
```
