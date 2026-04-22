#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PYTHON_BIN=".venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "[pre-commit] Python not found. Run tools/wsl/bootstrap.sh (WSL) or tools/windows/bootstrap.ps1 (Windows) first."
  exit 1
fi

echo "[pre-commit] Running ASO checks with $PYTHON_BIN..."
set +e
OUTPUT=$("$PYTHON_BIN" -m pytest -m aso -q 2>&1)
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "[pre-commit] ASO checks failed"
  echo "$OUTPUT"
  exit $STATUS
fi

echo "[pre-commit] ASO checks passed"
