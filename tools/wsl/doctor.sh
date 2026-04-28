#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

repo_root="$(wsl_repo_root)"
require_repo_root "$repo_root"
cd "$repo_root"

failures=()
warnings=()

write_check() {
    local label="$1"
    local ok="$2"
    local details="$3"
    local warning_only="${4:-0}"

    if [[ "$ok" == "1" ]]; then
        printf '[OK]   %s - %s\n' "$label" "$details"
        return
    fi

    if [[ "$warning_only" == "1" ]]; then
        warnings+=("$label")
        printf '[WARN] %s - %s\n' "$label" "$details"
        return
    fi

    failures+=("$label")
    printf '[FAIL] %s - %s\n' "$label" "$details"
}

uv_path="$(command -v uv || true)"
write_check "uv" "$(if [[ -n "$uv_path" ]]; then printf '1'; else printf '0'; fi)" "${uv_path:-not installed}"

lock_file="$repo_root/uv.lock"
write_check "uv.lock" "$(if [[ -f "$lock_file" ]]; then printf '1'; else printf '0'; fi)" "$lock_file"

venv_python="$(venv_python_path "$repo_root")"
has_venv="$(if [[ -x "$venv_python" ]]; then printf '1'; else printf '0'; fi)"
write_check ".venv" "$has_venv" "$venv_python"

if [[ "$has_venv" == "1" ]]; then
    python_version="$($venv_python --version 2>/dev/null || true)"
    expected_version="Python $(get_required_python_version "$repo_root")"
    write_check "python" "$(if [[ "$python_version" == "$expected_version" ]]; then printf '1'; else printf '0'; fi)" "$python_version"
fi

playwright_ok="0"
if compgen -G "$HOME/.cache/ms-playwright/chromium-*" >/dev/null; then
    playwright_ok="1"
fi
write_check "playwright chromium" "$playwright_ok" "Run bootstrap without --skip-playwright if missing." "1"

ui_dist_index="$repo_root/framework/visual/ui/dist/index.html"
write_check "report ui dist" "$(if [[ -f "$ui_dist_index" ]]; then printf '1'; else printf '0'; fi)" "$ui_dist_index"

docker_path="$(command -v docker || true)"
write_check "docker" "$(if [[ -n "$docker_path" ]]; then printf '1'; else printf '0'; fi)" "${docker_path:-required only for MinIO/grid helpers}" "1"

if (( ${#warnings[@]} > 0 )); then
    printf 'Warnings: %s\n' "$(IFS=', '; printf '%s' "${warnings[*]}")"
fi

if (( ${#failures[@]} > 0 )); then
    die "Doctor found blocking issues: $(IFS=', '; printf '%s' "${failures[*]}")"
fi

info "Doctor finished without blocking issues."
