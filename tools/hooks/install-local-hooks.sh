#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

mkdir -p "$HOOKS_DIR"
cp "$REPO_ROOT/tools/hooks/pre-commit-aso.sh" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "Installed local pre-commit hook: $HOOKS_DIR/pre-commit"
echo "It runs: python -m pytest -m aso -q"
