#!/usr/bin/env bash
set -euo pipefail

wsl_common_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

info() {
    printf '[INFO] %s\n' "$1"
}

warn() {
    printf '[WARN] %s\n' "$1"
}

die() {
    printf '[FAIL] %s\n' "$1" >&2
    exit 1
}

is_wsl() {
    if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
        return 0
    fi

    if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
        return 0
    fi

    return 1
}

require_wsl() {
    if ! is_wsl; then
        die "This setup supports WSL2 only. Open the repo in a WSL shell and rerun."
    fi
}

wsl_repo_root() {
    local root
    root="$(cd "$wsl_common_dir/../.." && pwd -P)"
    printf '%s' "$root"
}

require_repo_root() {
    local repo_root="$1"

    [[ -f "$repo_root/pyproject.toml" ]] || die "Missing pyproject.toml in $repo_root"
    [[ -f "$repo_root/.python-version" ]] || die "Missing .python-version in $repo_root"
}

get_required_python_version() {
    local repo_root="$1"
    local version

    read -r version < "$repo_root/.python-version"
    version="${version//[[:space:]]/}"
    [[ -n "$version" ]] || die ".python-version is empty"
    printf '%s' "$version"
}

ensure_uv() {
    if command -v uv >/dev/null 2>&1; then
        return
    fi

    command -v curl >/dev/null 2>&1 || die "curl is required to install uv"

    info "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"

    command -v uv >/dev/null 2>&1 || die "uv installation failed. Install uv manually and rerun."
}

venv_python_path() {
    local repo_root="$1"
    printf '%s/.venv/bin/python' "$repo_root"
}

ensure_repo_environment() {
    local repo_root="$1"
    local python_version

    python_version="$(get_required_python_version "$repo_root")"
    ensure_uv

    info "Installing Python $python_version via uv"
    uv python install "$python_version"

    info "Syncing dependencies from uv.lock"
    uv sync --frozen --managed-python --python "$python_version" --extra dev
}

ensure_bootstrap_ready() {
    local repo_root="$1"
    local python_path

    python_path="$(venv_python_path "$repo_root")"
    [[ -x "$python_path" ]] || die "Missing .venv. Run tools/wsl/bootstrap.sh first."
    ensure_uv
}

install_playwright_chromium() {
    local repo_root="$1"
    local python_path

    python_path="$(venv_python_path "$repo_root")"
    [[ -x "$python_path" ]] || die "Missing .venv Python. Run bootstrap first."

    info "Installing Playwright Chromium"
    "$python_path" -m playwright install chromium
}

install_local_hooks() {
    local repo_root="$1"
    local hook_installer

    hook_installer="$repo_root/tools/hooks/install-local-hooks.sh"
    if [[ -d "$repo_root/.git" && -x "$hook_installer" ]]; then
        "$hook_installer"
    fi
}
