---
name: commit
description: Conventional commits for Red Alert project. Enforces commit format and pre-commit validation.
argument-hint: "[scope]"
disable-model-invocation: true
---

Commit changes for $ARGUMENTS:

## Commit Format

```
type(scope): description

- Summary of changes

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Types

| Type | Purpose |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring (no behavior change) |
| `test` | Adding or updating tests only |
| `chore` | Maintenance, config, dependencies |
| `docs` | Documentation only |

### Scope

Use the affected area: `feat(ingestion): add Tzofar API client`, `fix(api): handle BOM in OREF responses`

## Pre-Commit Validation

Before committing, all tests must pass:

```bash
uv run pytest tests/ --tb=short
```

If tests fail, fix the issue and retry. Never use `--no-verify`.

## Protected Path Gate

**HITL required** when commit includes files in `.claude/`, `docs/`, database migrations, or `docker-compose.yml`.

## Single Responsibility

Each commit covers ONE feature or logical change. Do not bundle unrelated changes.
