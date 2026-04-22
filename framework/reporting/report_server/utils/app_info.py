from __future__ import annotations

import json
import settings
import settings_cli
import subprocess
import tomllib
from pathlib import Path
from typing import Any

from ..context import ReportServerContext


def _git_output(repo_root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return completed.stdout.strip()


def _runtime_version(repo_root: Path) -> str:
    version = _git_output(repo_root, ["describe", "--tags", "--always", "--dirty"])
    if version.startswith("v"):
        version = version[1:]
    return version or "unknown"


def _runtime_commit(repo_root: Path) -> str:
    commit = _git_output(repo_root, ["rev-parse", "--short", "HEAD"])
    return commit or "unknown"


def _pyproject_codename(repo_root: Path) -> str:
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return "unknown"
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except Exception:
        return "unknown"
    tool_section = data.get("tool") if isinstance(data, dict) else None
    app_section = tool_section.get("netqawner") if isinstance(tool_section, dict) else None
    codename = app_section.get("codename") if isinstance(app_section, dict) else ""
    return str(codename).strip() or "unknown"


def _read_ui_build_info(ui_dist_dir: Path) -> dict[str, str]:
    build_info_path = ui_dist_dir / "build-info.json"
    if not build_info_path.is_file():
        return {}
    try:
        raw = json.loads(build_info_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def _build_app_info_payload(context: ReportServerContext) -> dict[str, Any]:
    codename = _pyproject_codename(context.repo_root)
    runtime = {
        "version": _runtime_version(context.repo_root),
        "codename": codename,
        "commit": _runtime_commit(context.repo_root),
    }
    build_info = _read_ui_build_info(context.ui_dist_dir)
    ui_build_version = build_info.get("version") or build_info.get("ui_src_version") or runtime["version"]
    ui_build = {
        "version": ui_build_version,
        "codename": build_info.get("codename", codename),
        "ui_src_version": build_info.get("ui_src_version", "unknown"),
        "commit": build_info.get("commit", runtime["commit"]),
        "built_at": build_info.get("built_at", "unknown"),
    }
    ticket = str(getattr(settings_cli, "nn_ticket", "") or "").strip()
    if ticket.lower() == "none":
        ticket = ""
    default_note = str(getattr(settings_cli, "run_note", "") or "").strip()
    default_username = str(getattr(settings, "jira_username", "") or "").strip()
    default_password = str(getattr(settings, "jira_password", "") or "")
    return {
        "runtime": runtime,
        "ui_build": ui_build,
        "ui_config": {
            "pms_poll_interval_ms": max(100, int(context.pms_poll_interval_ms or 5000)),
            "pms_poll_idle_multiplier": max(1.0, float(context.pms_poll_idle_multiplier or 1.0)),
            "jira": {
                "enabled": bool(context.jira_enabled),
                "auth_mode": str(context.jira_auth_mode or "").strip() or "",
                "auth_configured": bool(context.jira_auth_configured),
                "default_ticket": ticket,
                "default_note": default_note,
                "default_username": default_username,
                "default_password": default_password,
                "default_mode": "auto",
                "framework_mode": str(getattr(context, "framework_mode", "server") or "server").strip().lower(),
                "submit_timeout_ms": max(10000, int(getattr(context, "jira_submit_timeout_ms", 120000) or 120000)),
            },
        },
    }
