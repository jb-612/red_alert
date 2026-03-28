#!/bin/bash
# Display session startup banner for Red Alert Analytics Dashboard.
set -euo pipefail

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
CWD=$(pwd)

echo "=================================================="
echo "  Red Alert Analytics Dashboard"
echo "=================================================="
echo ""
echo "Branch:   $BRANCH"
echo "CWD:      $CWD"
echo ""

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

# Show project structure status
echo "Project Status:"

if [[ -d "$REPO_ROOT/backend" ]]; then
  PY_COUNT=$(find "$REPO_ROOT/backend" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
  echo "  Backend:  $PY_COUNT Python files"
else
  echo "  Backend:  not scaffolded yet"
fi

if [[ -d "$REPO_ROOT/frontend" ]]; then
  echo "  Frontend: exists"
else
  echo "  Frontend: not scaffolded yet"
fi

DOC_COUNT=$(find "$REPO_ROOT/docs" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "  Docs:     $DOC_COUNT markdown files"

# Show test count if tests exist
if [[ -d "$REPO_ROOT/tests" ]]; then
  TEST_COUNT=$(find "$REPO_ROOT/tests" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
  echo "  Tests:    $TEST_COUNT test files"
fi

echo "=================================================="

exit 0
