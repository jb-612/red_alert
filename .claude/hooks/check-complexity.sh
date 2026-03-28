#!/usr/bin/env bash
set -euo pipefail
# PostToolUse hook for Edit|Write — check cyclomatic complexity
# Exit 0 = pass, Exit 2 = violation

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then exit 0; fi
if [[ "$FILE_PATH" != *.py ]]; then exit 0; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

# Only check production code under backend/
if [[ "$REL_PATH" != backend/* ]]; then exit 0; fi
# Skip test files
if [[ "$REL_PATH" == *test_* ]]; then exit 0; fi

# Run radon — show only CC > 5 (grade C and above)
VIOLATIONS=$(radon cc -s -n C "$FILE_PATH" 2>/dev/null || echo "")

if [ -n "$VIOLATIONS" ]; then
  echo "COMPLEXITY VIOLATION (CC > 5):" >&2
  echo "$VIOLATIONS" >&2
  echo "" >&2
  echo "Refactor to reduce cyclomatic complexity before committing." >&2
  exit 2
fi

exit 0
