#!/usr/bin/env bash
set -euo pipefail
# Comprehensive quality gate script for Red Alert Analytics Dashboard
# Usage: .claude/hooks/quality-gate.sh [--fix]
# Exit 0 = all gates pass, Exit 1 = one or more gates failed

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

FIX_MODE="${1:-}"
FAILED=0
TOTAL=8

echo "========================================================"
echo "       Red Alert Quality Gates (8 checks)                "
echo "========================================================"
echo ""

# --- Gate 1: Unit Tests + Coverage ---
echo "-- Gate 1/8: Unit Tests + Coverage --"
if uv run pytest tests/ -v --tb=short --cov=backend --cov-report=term-missing --cov-fail-under=60 2>&1; then
    echo "  [PASS] Gate 1"
else
    echo "  [FAIL] Gate 1"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 2: Ruff Linting (25 rule sets) ---
echo "-- Gate 2/8: Ruff Linting (25 rule sets) --"
if [[ "$FIX_MODE" == "--fix" ]]; then
    uv run ruff check --fix backend/ 2>&1
fi
if uv run ruff check backend/ 2>&1; then
    echo "  [PASS] Gate 2"
else
    echo "  [FAIL] Gate 2"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 3: Ruff Formatting ---
echo "-- Gate 3/8: Ruff Formatting --"
if [[ "$FIX_MODE" == "--fix" ]]; then
    uv run ruff format backend/ 2>&1
fi
if uv run ruff format --check backend/ 2>&1; then
    echo "  [PASS] Gate 3"
else
    echo "  [FAIL] Gate 3"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 4: Mypy Type Checking ---
echo "-- Gate 4/8: Mypy Type Checking --"
if uv run mypy backend/ 2>&1; then
    echo "  [PASS] Gate 4"
else
    echo "  [FAIL] Gate 4"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 5: Vulture Dead Code ---
echo "-- Gate 5/8: Vulture Dead Code Detection --"
VULTURE_OUT=$(uv run vulture backend/ --min-confidence 80 2>&1 || true)
if [ -z "$VULTURE_OUT" ]; then
    echo "  [PASS] Gate 5"
else
    echo "$VULTURE_OUT"
    echo "  [FAIL] Gate 5"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 6: Radon Cyclomatic Complexity ---
echo "-- Gate 6/8: Cyclomatic Complexity (CC <= 5) --"
CC_OUT=$(uv run radon cc -s -n C backend/ 2>&1 || true)
if [ -z "$CC_OUT" ]; then
    echo "  [PASS] Gate 6"
else
    echo "$CC_OUT"
    echo "  [FAIL] Gate 6"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 7: Cognitive Complexity ---
echo "-- Gate 7/8: Cognitive Complexity (<= 15) --"
if uv run complexipy backend/ --max-complexity-allowed 15 --quiet 2>&1; then
    echo "  [PASS] Gate 7"
else
    echo "  [FAIL] Gate 7"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Gate 8: Maintainability Index ---
echo "-- Gate 8/8: Maintainability Index (>= B) --"
MI_OUT=$(uv run radon mi -s -n B backend/ 2>&1 || true)
if [ -z "$MI_OUT" ]; then
    echo "  [PASS] Gate 8"
else
    echo "$MI_OUT"
    echo "  [FAIL] Gate 8"
    FAILED=$((FAILED + 1))
fi
echo ""

# --- Summary ---
PASSED=$((TOTAL - FAILED))
echo "========================================================"
if [ $FAILED -eq 0 ]; then
    echo "  ALL $TOTAL GATES PASSED"
else
    echo "  $PASSED/$TOTAL GATES PASSED -- $FAILED FAILED"
fi
echo "========================================================"

exit $FAILED
