---
name: testing
description: "Run comprehensive quality gates: tests with coverage, linting (25 rule sets), type checking, complexity, dead code. Use before commit."
argument-hint: "[scope or test-path]"
allowed-tools: Read, Glob, Grep, Bash
---

Run quality gates for $ARGUMENTS:

## Quality Gates (run in order, stop on first failure)

### Gate 1: Unit Tests with Coverage

```bash
uv run pytest tests/ -v --tb=short --cov=backend --cov-report=term-missing --cov-fail-under=60
```

Must pass with 0 failures. Coverage must meet threshold (currently 60%, target 80%).

### Gate 2: Expanded Linting (25 rule sets)

```bash
uv run ruff check backend/
```

Must be clean. Covers security, bugs, complexity, annotations, timezone
safety, performance, dead code, and more.

### Gate 3: Formatting Check

```bash
uv run ruff format --check backend/
```

Must be formatted. Run `uv run ruff format backend/` to auto-fix.

### Gate 4: Type Checking

```bash
uv run mypy backend/
```

Must have zero type errors (warnings allowed initially).

### Gate 5: Dead Code

```bash
uv run vulture backend/ --min-confidence 80
```

Must have zero high-confidence dead code findings.

### Gate 6: Cyclomatic Complexity

```bash
uv run radon cc -s -n C backend/
```

No functions above CC 5.

### Gate 7: Cognitive Complexity

```bash
uv run complexipy backend/ --max-complexity-allowed 15 --quiet
```

No functions above cognitive complexity 15.

### Gate 8: Maintainability Index

```bash
uv run radon mi -s -n B backend/
```

No files below MI grade B.

## Report Format

```
Quality Gates: [PASS/FAIL]
  1. Tests:        N passed, N failed | Coverage: NN% (threshold: 60%)
  2. Linting:      N issues (ruff, 25 rule sets)
  3. Formatting:   PASS/FAIL
  4. Type Check:   N errors (mypy)
  5. Dead Code:    N findings (vulture)
  6. CC:           N violations > 5 (radon)
  7. Cognitive:    N violations > 15 (complexipy)
  8. Maint. Index: N files below B (radon MI)
```

## Coverage Ratchet

Current threshold: 60%. When coverage consistently exceeds the threshold
by 5+ points, update `fail_under` in `[tool.coverage.report]` in
pyproject.toml. Target: 80%.

## Quick Run (quality-gate.sh)

For a single-command run of all 8 gates:

```bash
.claude/hooks/quality-gate.sh       # check only
.claude/hooks/quality-gate.sh --fix # auto-fix then check
```

## Cross-References

- `@commit` — Run `/testing` before committing
- `@code-review` — Runs same automated gates plus manual review
