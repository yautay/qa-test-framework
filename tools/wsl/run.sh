#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

repo_root="$(wsl_repo_root)"
require_repo_root "$repo_root"
cd "$repo_root"

command_name="${1:-doctor}"
if (($# > 0)); then
    shift
fi

normalized="$(printf '%s' "$command_name" | tr '[:upper:]' '[:lower:]')"
python_path="$(venv_python_path "$repo_root")"

case "$normalized" in
    bootstrap)
        "$script_dir/bootstrap.sh" "$@"
        ;;
    doctor)
        "$script_dir/doctor.sh" "$@"
        ;;
    sync)
        ensure_repo_environment "$repo_root"
        ;;
    report)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m framework.reporting.report_server "$@"
        ;;
    verify)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" framework/pytest_discovery_guard.py
        "$python_path" tools/scenarios/verify_scenarios.py
        ;;
    test)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m pytest -q "$@"
        ;;
    aso)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m pytest -m aso -q "$@"
        ;;
    api)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m pytest -m api -q "$@"
        ;;
    e2e)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m pytest -m e2e -q "$@"
        ;;
    visual)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m pytest -m visual -q "$@"
        ;;
    smoke)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m pytest -m smoke -q "$@"
        ;;
    lint)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m ruff check qa framework tools
        ;;
    format-check)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m black --check qa framework tools
        ;;
    typecheck)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m mypy qa framework tools
        ;;
    security)
        ensure_bootstrap_ready "$repo_root"
        "$python_path" -m bandit -r -x qa --skip B101,B105,B106,B110,B112,B404,B603,B607,B311 framework tools
        "$python_path" -m pip_audit
        ;;
    *)
        die "Unknown command '$command_name'. Supported: bootstrap, doctor, sync, report, verify, test, aso, api, e2e, visual, smoke, lint, format-check, typecheck, security"
        ;;
esac
