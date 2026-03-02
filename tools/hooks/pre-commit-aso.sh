#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "[pre-commit] Running ASO checks..."
set +e
OUTPUT=$(make test-aso 2>&1)
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "[pre-commit] ASO checks failed"
  echo "$OUTPUT"
  exit $STATUS
fi

echo "[pre-commit] ASO checks passed"
