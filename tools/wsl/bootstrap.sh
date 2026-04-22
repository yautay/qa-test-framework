#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

skip_playwright=0
reinstall=0

for arg in "$@"; do
    case "$arg" in
        --skip-playwright)
            skip_playwright=1
            ;;
        --reinstall)
            reinstall=1
            ;;
        *)
            die "Unknown argument '$arg'. Supported: --skip-playwright, --reinstall"
            ;;
    esac
done

require_wsl

repo_root="$(wsl_repo_root)"
require_repo_root "$repo_root"
cd "$repo_root"

if [[ "$reinstall" -eq 1 && -d "$repo_root/.venv" ]]; then
    info "Removing existing .venv"
    rm -rf "$repo_root/.venv"
fi

ensure_repo_environment "$repo_root"
install_local_hooks "$repo_root"

if [[ "$skip_playwright" -eq 0 ]]; then
    install_playwright_chromium "$repo_root"
fi

info "Bootstrap completed."
printf 'Repo root: %s\n' "$repo_root"
printf 'Python: %s\n' "$(get_required_python_version "$repo_root")"
printf 'Venv: %s\n' "$repo_root/.venv"
printf 'Pre-commit hook: %s\n' "$repo_root/.git/hooks/pre-commit"
printf 'Next: bash tools/wsl/run.sh doctor\n'
