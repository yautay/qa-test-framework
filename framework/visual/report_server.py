from __future__ import annotations

from argparse import ArgumentParser
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
from secrets import token_urlsafe
import subprocess
from threading import Lock
from typing import Any, cast
from urllib.parse import parse_qs, unquote, urlparse
import json
import mimetypes
import re
import sys
import time
import tomllib

from loguru import logger

try:
    import reportlab.lib.pagesizes as _r_pagesizes
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    _REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _r_pagesizes = None
    ImageReader = None  # type: ignore[assignment]
    canvas = None  # type: ignore[assignment]
    _REPORTLAB_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.reporting_client import ReportingClient
from framework.visual.baseline_store import BaselineStore
from framework.visual.config.server import REPORT_SYNC_WORKERS
from framework.visual.perceptual_client import PMSClient, PMSClientError


DEFAULT_PORT = 4173
CHALLENGE_TTL_SECONDS = 300
_RUN_ID_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")
_READY_MARKER = ".report-ready.json"
_PERCEPTUAL_STATUS = "perceptual-status.json"
LOCK_TTL_SECONDS = 110
TEXT_MAX_LENGTH = 500
_TEXT_CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


@dataclass
class ChallengeEntry:
    run_id: str
    phrase: str
    expires_at: float


@dataclass
class ReportServerContext:
    repo_root: Path
    ui_dist_dir: Path
    baseline_store: BaselineStore
    run_dirs: dict[str, Path]
    pinned_run_dirs: dict[str, Path] = field(default_factory=dict)
    challenges: dict[str, ChallengeEntry] = field(default_factory=dict)
    reporting_client: ReportingClient | None = None
    reporting_enabled: bool = False
    reporting_bug_endpoint: str = ""
    reporting_aso_endpoint: str = ""
    bug_pdf_config_path: Path | None = None
    sync_workers: int = 0
    sync_executor: ThreadPoolExecutor | None = field(default=None, repr=False)
    pms_enabled: bool = False
    pms_base_url: str = ""
    pms_timeout_sec: int = 15
    pms_health_timeout_seconds: int = 2
    pms_retry_max: int = 2
    _lock: Any = field(default_factory=Lock)

    def resolve_run_dir(self, run_id: str) -> Path | None:
        with self._lock:
            existing = self.run_dirs.get(run_id)
            if existing is not None:
                return existing
        self.refresh_run_dirs()
        with self._lock:
            return self.run_dirs.get(run_id)

    def refresh_run_dirs(self) -> None:
        discovered = _discover_visual_run_dirs(self.repo_root)
        for run_id, report_dir in self.pinned_run_dirs.items():
            if _is_ready_visual_dir(report_dir):
                discovered[run_id] = report_dir
        with self._lock:
            self.run_dirs = discovered

    def list_run_dirs(self) -> dict[str, Path]:
        self.refresh_run_dirs()
        with self._lock:
            return dict(self.run_dirs)


def _latest_visual_report_dir(repo_root: Path) -> Path:
    artifacts_root = repo_root / "artifacts"
    if not artifacts_root.is_dir():
        raise FileNotFoundError("artifacts directory not found")

    candidates = sorted(
        [path / "visual" for path in artifacts_root.iterdir() if path.is_dir() and (path / "visual").is_dir()]
    )
    if not candidates:
        raise FileNotFoundError("no visual reports found under artifacts/<run_id>/visual")
    return candidates[-1]


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
    ui_build = {
        "version": build_info.get("version", "unknown"),
        "codename": build_info.get("codename", codename),
        "ui_src_version": build_info.get("ui_src_version", "unknown"),
        "commit": build_info.get("commit", "unknown"),
        "built_at": build_info.get("built_at", "unknown"),
    }
    return {
        "runtime": runtime,
        "ui_build": ui_build,
    }


def _resolve_report_dir(repo_root: Path, report_dir: str | None, run_id: str | None) -> Path:
    if run_id:
        candidate = (repo_root / "artifacts" / run_id / "visual").resolve()
        if not candidate.is_dir():
            raise FileNotFoundError(f"visual report directory not found for run_id={run_id!r}: {candidate}")
        return candidate

    if report_dir:
        candidate = Path(report_dir)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if not candidate.is_dir():
            raise FileNotFoundError(f"visual report directory not found: {candidate}")
        return candidate

    return _latest_visual_report_dir(repo_root)


def _run_id_from_visual_dir(repo_root: Path, report_dir: Path) -> str:
    try:
        rel = report_dir.resolve().relative_to((repo_root / "artifacts").resolve())
        parts = rel.parts
        if len(parts) >= 2 and parts[1] == "visual" and _RUN_ID_SAFE.match(parts[0]):
            return parts[0]
    except Exception:
        pass
    fallback = report_dir.parent.name.strip() or report_dir.name.strip() or "report"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", fallback)


def _discover_visual_run_dirs(repo_root: Path) -> dict[str, Path]:
    artifacts_root = repo_root / "artifacts"
    if not artifacts_root.is_dir():
        return {}
    out: dict[str, Path] = {}
    for run_dir in artifacts_root.iterdir():
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        if not _RUN_ID_SAFE.match(run_id):
            continue
        visual_dir = (run_dir / "visual").resolve()
        if _is_ready_visual_dir(visual_dir):
            out[run_id] = visual_dir
    return out


def _is_ready_visual_dir(visual_dir: Path) -> bool:
    if not visual_dir.is_dir():
        return False
    return (visual_dir / _READY_MARKER).is_file()


def _read_results_rows(report_dir: Path) -> list[dict[str, Any]]:
    results_path = report_dir / "results.json"
    if not results_path.is_file():
        return []
    try:
        data = json.loads(results_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = data.get("results") if isinstance(data, dict) else []
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)]


def _read_run_metadata(report_dir: Path) -> dict[str, str]:
    candidate = report_dir.parent / "run-metadata.json"
    if not candidate.is_file():
        return {"tester": "", "run_note": ""}
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return {"tester": "", "run_note": ""}
    if not isinstance(data, dict):
        return {"tester": "", "run_note": ""}
    return {
        "tester": str(data.get("tester", "") or "").strip(),
        "run_note": str(data.get("run_note", "") or "").strip(),
    }


def _summarize_perceptual_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    total = 0
    pending = 0
    done = 0
    error = 0
    for row in rows:
        perceptual = row.get("perceptual") if isinstance(row, dict) else None
        if not isinstance(perceptual, dict):
            continue
        status = str(perceptual.get("status", "")).strip().lower()
        if not status or status == "skipped":
            continue
        total += 1
        if status in {"queued", "running"}:
            pending += 1
        elif status == "done":
            done += 1
        elif status in {"error", "timeout"}:
            error += 1
    return {
        "total_count": total,
        "pending_count": pending,
        "done_count": done,
        "error_count": error,
        "in_progress": 1 if pending > 0 else 0,
    }


def _read_perceptual_status(report_dir: Path, rows: list[dict[str, Any]]) -> dict[str, int]:
    fallback = _summarize_perceptual_from_rows(rows)
    status_path = report_dir / _PERCEPTUAL_STATUS
    if not status_path.is_file():
        return fallback
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return fallback
    if not isinstance(payload, dict):
        return fallback
    return {
        "total_count": int(payload.get("total_count", fallback["total_count"]) or 0),
        "pending_count": int(payload.get("pending_count", fallback["pending_count"]) or 0),
        "done_count": int(payload.get("done_count", fallback["done_count"]) or 0),
        "error_count": int(payload.get("error_count", fallback["error_count"]) or 0),
        "in_progress": 1 if bool(payload.get("in_progress", False)) else 0,
    }


def _report_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    failed = 0
    passed = 0
    uncertain = 0
    skipped = 0
    new_count = 0
    for row in rows:
        status = str(row.get("status", "")).strip().lower()
        if status == "failed":
            failed += 1
        elif status == "passed":
            passed += 1
        elif status == "uncertain":
            uncertain += 1
        elif status == "skipped":
            skipped += 1
        elif status == "new":
            new_count += 1
    return {
        "total": len(rows),
        "failed": failed,
        "passed": passed,
        "uncertain": uncertain,
        "skipped": skipped,
        "new": new_count,
    }


def _list_reports_payload(context: ReportServerContext) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    run_dirs = context.list_run_dirs()
    for run_id, report_dir in sorted(run_dirs.items(), key=lambda item: item[0], reverse=True):
        rows = _read_results_rows(report_dir)
        run_metadata = _read_run_metadata(report_dir)
        stats = _report_summary(rows)
        pms_stats = _read_perceptual_status(report_dir, rows)
        try:
            updated_at = int(report_dir.stat().st_mtime)
        except Exception:
            updated_at = 0

        build_dir = report_dir.parent
        with context._lock:
            state = _load_state(build_dir)
            if not context.reporting_enabled:
                synced_cases, sent_events = _treat_reporting_disabled_as_success(state)
                if synced_cases > 0 or sent_events > 0:
                    _save_state(build_dir, state)
        test_cases = state.get("test_cases", {})
        outbox = state.get("outbox", [])

        bug_count = sum(1 for tc in test_cases.values() if isinstance(tc, dict) and tc.get("bug", {}).get("locked"))
        asso_count = sum(1 for tc in test_cases.values() if isinstance(tc, dict) and tc.get("aso", {}).get("locked"))
        note_count = sum(
            1
            for tc in test_cases.values()
            if isinstance(tc, dict) and (tc.get("bug", {}).get("note") or tc.get("aso", {}).get("note"))
        )
        sync_unsynced_count = sum(
            1
            for tc in test_cases.values()
            if isinstance(tc, dict)
            and (
                (tc.get("bug", {}).get("locked") and not tc.get("bug", {}).get("synced"))
                or (tc.get("aso", {}).get("locked") and not tc.get("aso", {}).get("synced"))
            )
        )

        sync_failed_count = 0
        sync_pending_count = 0
        sync_sending_count = 0
        for entry in outbox:
            if not isinstance(entry, dict):
                continue
            event_type = str(entry.get("type", "")).upper()
            if event_type not in {"BUG_SET", "ASO_SET"}:
                continue
            status = str(entry.get("status", "pending")).lower()
            if status == "failed":
                sync_failed_count += 1
            elif status == "pending":
                sync_pending_count += 1
            elif status == "sending":
                sync_sending_count += 1

        has_sync_issues = bool(
            sync_unsynced_count > 0 or sync_failed_count > 0 or sync_pending_count > 0 or sync_sending_count > 0
        )

        reports.append(
            {
                "run_id": run_id,
                "report_dir": str(report_dir),
                "updated_at_epoch": updated_at,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(updated_at)) if updated_at else "",
                "total": stats["total"],
                "failed": stats["failed"],
                "passed": stats["passed"],
                "uncertain": stats["uncertain"],
                "skipped": stats["skipped"],
                "new": stats["new"],
                "tester": run_metadata.get("tester", ""),
                "run_note": run_metadata.get("run_note", ""),
                "bug_count": bug_count,
                "aso_count": asso_count,
                "note_count": note_count,
                "has_sync_issues": has_sync_issues,
                "sync_unsynced_count": sync_unsynced_count,
                "sync_failed_count": sync_failed_count,
                "sync_pending_count": sync_pending_count,
                "sync_sending_count": sync_sending_count,
                "pms_total_count": pms_stats["total_count"],
                "pms_pending_count": pms_stats["pending_count"],
                "pms_done_count": pms_stats["done_count"],
                "pms_success_count": pms_stats["done_count"],
                "pms_error_count": pms_stats["error_count"],
                "pms_in_progress": bool(pms_stats["in_progress"]),
            }
        )
    return reports


def _perceptual_queue_payload(context: ReportServerContext) -> dict[str, Any]:
    if not context.pms_enabled or not str(context.pms_base_url).strip():
        return {
            "enabled": False,
            "base_url": "",
            "server_active": 0,
            "queued": 0,
            "running": 0,
            "done": 0,
            "error": 0,
            "total": 0,
            "updated_at_epoch": int(time.time()),
            "error_message": "pms disabled",
        }

    client = PMSClient(
        base_url=context.pms_base_url,
        timeout_seconds=context.pms_timeout_sec,
        health_timeout_seconds=context.pms_health_timeout_seconds,
        retry_max=context.pms_retry_max,
    )

    try:
        jobs = client.list_jobs()
    except PMSClientError as exc:
        return {
            "enabled": True,
            "base_url": context.pms_base_url,
            "server_active": 0,
            "queued": 0,
            "running": 0,
            "done": 0,
            "error": 0,
            "total": 0,
            "updated_at_epoch": int(time.time()),
            "error_message": str(exc),
        }

    queued = 0
    running = 0
    done = 0
    error = 0
    for job in jobs:
        status = str(job.get("status", "")).strip().lower()
        if status == "queued":
            queued += 1
        elif status == "running":
            running += 1
        elif status == "done":
            done += 1
        elif status == "error":
            error += 1
    return {
        "enabled": True,
        "base_url": context.pms_base_url,
        "server_active": queued + running,
        "queued": queued,
        "running": running,
        "done": done,
        "error": error,
        "total": len(jobs),
        "updated_at_epoch": int(time.time()),
        "error_message": None,
    }


def _perceptual_health_payload(context: ReportServerContext) -> dict[str, Any]:
    checked_at_epoch = int(time.time())
    if not context.pms_enabled or not str(context.pms_base_url).strip():
        return {
            "enabled": False,
            "base_url": "",
            "ok": False,
            "status_code": 0,
            "payload": {},
            "error_message": "pms disabled",
            "checked_at_epoch": checked_at_epoch,
        }

    client = PMSClient(
        base_url=context.pms_base_url,
        timeout_seconds=context.pms_timeout_sec,
        health_timeout_seconds=context.pms_health_timeout_seconds,
        retry_max=context.pms_retry_max,
    )

    try:
        details = client.get_health()
    except PMSClientError as exc:
        return {
            "enabled": True,
            "base_url": context.pms_base_url,
            "ok": False,
            "status_code": 0,
            "payload": {},
            "error_message": str(exc),
            "checked_at_epoch": checked_at_epoch,
        }

    payload = details.get("payload") if isinstance(details, dict) else {}
    if not isinstance(payload, dict):
        payload = {}

    return {
        "enabled": True,
        "base_url": context.pms_base_url,
        "ok": bool(details.get("ok")),
        "status_code": int(details.get("status_code", 0) or 0),
        "payload": payload,
        "error_message": str(details.get("error_message") or "").strip() or None,
        "checked_at_epoch": checked_at_epoch,
    }


def _cleanup_expired_challenges(context: ReportServerContext) -> None:
    now = time.time()
    with context._lock:
        expired = [challenge_id for challenge_id, item in context.challenges.items() if item.expires_at <= now]
        for challenge_id in expired:
            context.challenges.pop(challenge_id, None)


def _generate_phrase() -> str:
    adjectives = ["amber", "calm", "delta", "frozen", "gentle", "rapid", "silent", "solar"]
    nouns = ["anchor", "bridge", "cloud", "forest", "harbor", "river", "signal", "valley"]
    idx = int(time.time() * 1000) % 100
    return f"{adjectives[idx % len(adjectives)]}-{nouns[(idx // 2) % len(nouns)]}-{idx:02d}"


def _resolve_actual_png(report_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (report_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(report_dir)
    except ValueError as exc:
        raise ValueError(f"actual_path outside report directory: {raw_path}") from exc

    if candidate.suffix.lower() != ".png":
        raise ValueError(f"actual_path must be a .png file: {raw_path}")
    if not candidate.is_file():
        raise ValueError(f"actual_path not found: {raw_path}")
    return candidate


def _as_non_empty_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid field: {key}")
    return value.strip()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")


def _normalize_text(value: Any, *, trim: bool = True) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _TEXT_CONTROL_CHAR_REGEX.sub("", normalized)
    if trim:
        normalized = normalized.strip()
    return normalized


def _validated_text(value: Any, field_name: str) -> str:
    text = _normalize_text(value, trim=True)
    if len(text) > TEXT_MAX_LENGTH:
        raise ValueError(f"{field_name} exceeds {TEXT_MAX_LENGTH} characters")
    return text


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _content_type_for_path(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type:
        return mime_type
    return "application/octet-stream"


def _serve_file(handler: BaseHTTPRequestHandler, path: Path) -> None:
    if not path.is_file():
        handler.send_error(HTTPStatus.NOT_FOUND, "not found")
        return
    body = path.read_bytes()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", _content_type_for_path(path))
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _safe_run_id_or_error(raw_run_id: str) -> str:
    run_id = unquote(raw_run_id or "").strip()
    if not run_id or not _RUN_ID_SAFE.match(run_id):
        raise ValueError("invalid run_id")
    return run_id


def _build_dir(repo_root: Path, run_id: str) -> Path:
    artifacts_root = (repo_root / "artifacts").resolve()
    build_dir = (artifacts_root / run_id).resolve()
    try:
        build_dir.relative_to(artifacts_root)
    except ValueError as exc:
        raise ValueError("invalid build directory") from exc
    if not build_dir.is_dir():
        raise FileNotFoundError("build not found")
    return build_dir


def _lock_file_path(build_dir: Path) -> Path:
    return build_dir / "build.lock.json"


def _read_lock(build_dir: Path) -> dict[str, Any] | None:
    lock_path = _lock_file_path(build_dir)
    if not lock_path.is_file():
        return None
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _is_lock_expired(lock_data: dict[str, Any], now: float) -> bool:
    try:
        return float(lock_data.get("expires_at", 0)) <= now
    except Exception:
        return True


def _write_lock(build_dir: Path, payload: dict[str, Any]) -> None:
    _atomic_write_json(_lock_file_path(build_dir), payload)


def _acquire_lock(
    build_dir: Path,
    client_id: str,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    timestamp = time.time() if now is None else float(now)
    existing = _read_lock(build_dir)
    if existing and not _is_lock_expired(existing, timestamp):
        if str(existing.get("owner_client_id", "")) != client_id:
            return {"accepted": False, "reason": "locked", "lock": existing}
        lock_id = str(existing.get("lock_id") or "") or token_urlsafe(12)
        updated = {
            "build_id": str(existing.get("build_id") or ""),
            "lock_id": lock_id,
            "owner_client_id": client_id,
            "created_at": float(existing.get("created_at") or timestamp),
            "last_heartbeat_at": timestamp,
            "expires_at": timestamp + LOCK_TTL_SECONDS,
        }
        _write_lock(build_dir, updated)
        return {"accepted": True, "lock": updated}

    lock_id = token_urlsafe(12)
    payload = {
        "build_id": build_dir.name,
        "lock_id": lock_id,
        "owner_client_id": client_id,
        "created_at": timestamp,
        "last_heartbeat_at": timestamp,
        "expires_at": timestamp + LOCK_TTL_SECONDS,
    }
    _write_lock(build_dir, payload)
    return {"accepted": True, "lock": payload}


def _heartbeat_lock(
    build_dir: Path,
    client_id: str,
    lock_id: str,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    timestamp = time.time() if now is None else float(now)
    existing = _read_lock(build_dir)
    if not existing or _is_lock_expired(existing, timestamp):
        return {"accepted": False, "reason": "expired"}
    if str(existing.get("owner_client_id", "")) != client_id:
        return {"accepted": False, "reason": "owner_mismatch", "lock": existing}
    if str(existing.get("lock_id", "")) != lock_id:
        return {"accepted": False, "reason": "lock_mismatch", "lock": existing}
    updated = {
        "build_id": str(existing.get("build_id") or build_dir.name),
        "lock_id": lock_id,
        "owner_client_id": client_id,
        "created_at": float(existing.get("created_at") or timestamp),
        "last_heartbeat_at": timestamp,
        "expires_at": timestamp + LOCK_TTL_SECONDS,
    }
    _write_lock(build_dir, updated)
    return {"accepted": True, "lock": updated}


def _release_lock(build_dir: Path, client_id: str, lock_id: str) -> dict[str, Any]:
    existing = _read_lock(build_dir)
    if not existing:
        return {"accepted": True}
    if str(existing.get("owner_client_id", "")) != client_id:
        return {"accepted": False, "reason": "owner_mismatch"}
    if str(existing.get("lock_id", "")) != lock_id:
        return {"accepted": False, "reason": "lock_mismatch"}
    try:
        _lock_file_path(build_dir).unlink(missing_ok=True)
    except Exception:
        pass
    return {"accepted": True}


def _state_file_path(build_dir: Path) -> Path:
    return build_dir / "state.json"


def _empty_case_state() -> dict[str, Any]:
    return {
        "bug": {"locked": False, "synced": False, "note": ""},
        "aso": {"locked": False, "synced": False, "note": ""},
    }


def _normalize_case_state(raw: Any) -> dict[str, Any]:
    base = raw if isinstance(raw, dict) else {}
    bug = cast(dict[str, Any], base.get("bug")) if isinstance(base.get("bug"), dict) else {}
    aso = cast(dict[str, Any], base.get("aso")) if isinstance(base.get("aso"), dict) else {}
    bug_note = _normalize_text(bug.get("note"), trim=True)[:TEXT_MAX_LENGTH]
    aso_note = _normalize_text(aso.get("note"), trim=True)[:TEXT_MAX_LENGTH]
    return {
        "bug": {"locked": bool(bug.get("locked", False)), "synced": bool(bug.get("synced", False)), "note": bug_note},
        "aso": {"locked": bool(aso.get("locked", False)), "synced": bool(aso.get("synced", False)), "note": aso_note},
    }


def _normalize_outbox_entry(raw: Any) -> dict[str, Any]:
    base = raw if isinstance(raw, dict) else {}
    payload = base.get("payload") if isinstance(base.get("payload"), dict) else {}
    return {
        "event_id": str(base.get("event_id", "")),
        "type": str(base.get("type", "")),
        "payload": payload,
        "status": str(base.get("status", "pending")),
        "attempts": int(base.get("attempts", 0) or 0),
        "last_attempt_at": str(base.get("last_attempt_at", "")),
        "sent_at": str(base.get("sent_at", "")),
        "last_error": str(base.get("last_error", "")),
        "test_case_id": str(base.get("test_case_id", "")),
    }


def _load_state(build_dir: Path) -> dict[str, Any]:
    state_path = _state_file_path(build_dir)
    if not state_path.is_file():
        return {"test_cases": {}, "outbox": []}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"test_cases": {}, "outbox": []}
    if not isinstance(data, dict):
        return {"test_cases": {}, "outbox": []}
    test_cases = cast(dict[str, Any], data.get("test_cases")) if isinstance(data.get("test_cases"), dict) else {}
    outbox = cast(list[dict[str, Any]], data.get("outbox")) if isinstance(data.get("outbox"), list) else []
    normalized_cases: dict[str, Any] = {}
    for key, value in test_cases.items():
        if not isinstance(key, str):
            continue
        normalized_cases[key] = _normalize_case_state(value)
    normalized_outbox = [_normalize_outbox_entry(item) for item in outbox if isinstance(item, dict)]
    return {"test_cases": normalized_cases, "outbox": normalized_outbox}


def _save_state(build_dir: Path, state: dict[str, Any]) -> None:
    _atomic_write_json(_state_file_path(build_dir), state)


def _ensure_case_state(state: dict[str, Any], case_id: str) -> dict[str, Any]:
    cases = state.setdefault("test_cases", {})
    existing = cases.get(case_id)
    if isinstance(existing, dict):
        normalized = _normalize_case_state(existing)
        cases[case_id] = normalized
        return normalized
    normalized = _empty_case_state()
    cases[case_id] = normalized
    return normalized


def _default_pdf_config() -> dict[str, Any]:
    return {
        "fields": [
            {"label": "run.tester", "path": "run.tester", "required": True},
            {"label": "run.run_note", "path": "run.run_note", "required": True},
            {"label": "scenario.name", "path": "scenario.name", "required": True},
            {"label": "scenario.suite_id", "path": "scenario.suite_id", "required": True},
            {"label": "scenario.target_url", "path": "scenario.target_url", "required": True},
            {"label": "scenario.viewport", "path": "scenario.viewport", "required": True},
            {"label": "scenario.browser", "path": "scenario.browser", "required": True},
            {"label": "scenario.capture.selector", "path": "scenario.capture.selector", "required": False},
            {"label": "Notatka BUG", "path": "bug.note", "required": False},
            {"label": "Notatka ASO", "path": "aso.note", "required": False},
        ],
        "images": [
            {"label": "baseline", "path": "image.baseline"},
            {"label": "actual", "path": "image.actual"},
            {"label": "diff", "path": "image.diff"},
            {"label": "heatmap", "path": "image.heatmap"},
        ],
    }


def _load_bug_pdf_config(config_path: Path | None) -> dict[str, Any]:
    cfg = _default_pdf_config()
    if config_path is None or not config_path.is_file():
        return cfg
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("bug pdf config invalid json", path=str(config_path))
        return cfg
    if not isinstance(data, dict):
        return cfg
    merged = dict(cfg)
    if isinstance(data.get("fields"), list):
        merged["fields"] = data["fields"]
    if isinstance(data.get("images"), list):
        merged["images"] = data["images"]
    return merged


def _row_tag_key(row: dict[str, Any]) -> str:
    return "::".join(
        [
            str(row.get("scenario_id", "") or ""),
            str(row.get("actual_path", "") or ""),
            str(row.get("baseline_path", "") or ""),
            str(row.get("diff_path", "") or ""),
        ]
    )


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _apply_event_to_state(
    state: dict[str, Any],
    case_id: str,
    event_type: str,
    note_content: str | None,
) -> dict[str, Any]:
    case_state = _ensure_case_state(state, case_id)
    if event_type == "BUG_SET":
        case_state["bug"]["locked"] = True
        case_state["bug"]["synced"] = False
        case_state["bug"]["note"] = note_content or ""
    elif event_type == "ASO_SET":
        case_state["aso"]["locked"] = True
        case_state["aso"]["synced"] = False
        case_state["aso"]["note"] = note_content or ""
    return case_state


def _reporting_endpoint_for_event(context: ReportServerContext, event_type: str) -> str:
    if event_type == "BUG_SET":
        return context.reporting_bug_endpoint
    if event_type == "ASO_SET":
        return context.reporting_aso_endpoint
    return ""


def _send_outbox_event(
    *,
    context: ReportServerContext,
    run_id: str,
    rows_by_key: dict[str, dict[str, Any]],
    state: dict[str, Any],
    event: dict[str, Any],
) -> tuple[bool, str]:
    if not context.reporting_enabled:
        return False, "reporting disabled"
    event_type = str(event.get("type", ""))
    endpoint = _reporting_endpoint_for_event(context, event_type)
    if not endpoint:
        return False, "endpoint not configured"
    if context.reporting_client is None:
        return False, "reporting client unavailable"

    case_id = str(event.get("test_case_id", ""))
    case_state = _ensure_case_state(state, case_id)
    row = rows_by_key.get(case_id)
    if row is None:
        return False, "test case not found"

    payload_note = _normalize_text(event.get("payload", {}).get("note"), trim=True)

    tag = "BUG" if event_type == "BUG_SET" else "ASO"
    event_type_name = "visual_report"
    req = _build_reporting_payload(
        run_id,
        tag,
        row,
        case_state,
        event_type=event_type_name,
        event_note=payload_note,
        event_id=str(event.get("event_id", "")) or None,
    )
    accepted = bool(cast(Any, context.reporting_client).send_payload(endpoint, req))
    if accepted:
        return True, ""
    return False, "api rejected"


def _record_event_attempt(event: dict[str, Any], accepted: bool, error: str) -> None:
    timestamp = _utc_timestamp()
    event["attempts"] = int(event.get("attempts", 0) or 0) + 1
    event["last_attempt_at"] = timestamp
    if accepted:
        event["status"] = "sent"
        event["sent_at"] = timestamp
        event["last_error"] = ""
    else:
        event["status"] = "failed"
        event["last_error"] = error


def _mark_case_synced(case_state: dict[str, Any], event_type: str) -> None:
    if event_type == "BUG_SET":
        case_state["bug"]["synced"] = True
    elif event_type == "ASO_SET":
        case_state["aso"]["synced"] = True


def _is_reporting_tag_event(event_type: str) -> bool:
    return event_type in {"BUG_SET", "ASO_SET"}


def _treat_reporting_disabled_as_success(state: dict[str, Any]) -> tuple[int, int]:
    synced_cases = 0
    sent_events = 0

    test_cases = state.get("test_cases", {})
    if isinstance(test_cases, dict):
        for case_id, raw_case in test_cases.items():
            if not isinstance(case_id, str):
                continue
            case_state = _ensure_case_state(state, case_id)
            bug = case_state.get("bug", {}) if isinstance(case_state.get("bug"), dict) else {}
            aso = case_state.get("aso", {}) if isinstance(case_state.get("aso"), dict) else {}

            changed = False
            if bool(bug.get("locked")) and not bool(bug.get("synced")):
                case_state["bug"]["synced"] = True
                changed = True
            if bool(aso.get("locked")) and not bool(aso.get("synced")):
                case_state["aso"]["synced"] = True
                changed = True
            if changed:
                synced_cases += 1

    outbox = state.get("outbox", [])
    if isinstance(outbox, list):
        for entry in outbox:
            if not isinstance(entry, dict):
                continue
            event_type = str(entry.get("type", "")).upper()
            if not _is_reporting_tag_event(event_type):
                continue
            status = str(entry.get("status", "pending")).lower()
            if status in {"sent", "superseded"}:
                continue
            _record_event_attempt(entry, True, "")
            sent_events += 1

    return synced_cases, sent_events


def _resolve_sync_workers(configured_workers: int | None) -> int:
    cpu = os.cpu_count() or 2
    auto_workers = min(12, max(2, cpu * 2))
    if configured_workers is None:
        return auto_workers
    try:
        requested = int(configured_workers)
    except Exception:
        return auto_workers
    if requested <= 0:
        return auto_workers
    return requested


def _process_outbox_event(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    rows_by_key: dict[str, dict[str, Any]],
    event_id: str,
) -> None:
    build_dir = report_dir.parent
    event_snapshot: dict[str, Any] | None = None
    state_snapshot: dict[str, Any] = {}

    with context._lock:
        state_for_claim = _load_state(build_dir)
        outbox_for_claim = state_for_claim.get("outbox", [])
        event_for_claim = next((e for e in outbox_for_claim if str(e.get("event_id", "")) == event_id), None)
        if event_for_claim is None:
            return
        if str(event_for_claim.get("status", "")).lower() not in {"pending", "failed"}:
            return
        event_for_claim["status"] = "sending"
        event_snapshot = dict(event_for_claim)
        state_snapshot = state_for_claim
        _save_state(build_dir, state_for_claim)

    if event_snapshot is None:
        return

    accepted, error = _send_outbox_event(
        context=context,
        run_id=run_id,
        rows_by_key=rows_by_key,
        state=state_snapshot,
        event=event_snapshot,
    )

    with context._lock:
        state_after_send = _load_state(build_dir)
        outbox_after_send = state_after_send.get("outbox", [])
        event_after_send = next((e for e in outbox_after_send if str(e.get("event_id", "")) == event_id), None)
        if event_after_send is None:
            return
        current_status = str(event_after_send.get("status", "")).lower()
        if current_status not in {"sending", "pending", "failed"}:
            return
        _record_event_attempt(event_after_send, accepted, error)
        if accepted:
            case_state = _ensure_case_state(state_after_send, str(event_after_send.get("test_case_id", "")))
            _mark_case_synced(case_state, str(event_after_send.get("type", "")))
        _save_state(build_dir, state_after_send)


def _schedule_outbox_event(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    rows_by_key: dict[str, dict[str, Any]],
    event_id: str,
) -> Future[Any] | None:
    executor = context.sync_executor
    if executor is None:
        return None
    return executor.submit(
        _process_outbox_event,
        context=context,
        run_id=run_id,
        report_dir=report_dir,
        rows_by_key=rows_by_key,
        event_id=event_id,
    )


def _flush_pending(
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    *,
    wait_for_completion: bool = True,
) -> dict[str, Any]:
    build_dir = report_dir.parent

    event_ids_to_send: list[str] = []
    rows_by_key: dict[str, dict[str, Any]] = {}
    state: dict[str, Any] = {}

    with context._lock:
        state = _load_state(build_dir)
        rows = _read_results_rows(report_dir)
        rows_by_key = {_row_tag_key(row): row for row in rows}
        for event in state.get("outbox", []):
            if event.get("status") not in {"pending", "failed"}:
                continue
            event_id = str(event.get("event_id", "")).strip()
            if event_id:
                event_ids_to_send.append(event_id)

        if not context.reporting_enabled:
            synced_cases, sent_events = _treat_reporting_disabled_as_success(state)
            if synced_cases > 0 or sent_events > 0:
                _save_state(build_dir, state)
            logger.debug(
                "reporting_api_disabled_skipping_sync",
                run_id=run_id,
                source="report_flush",
                events_count=sent_events,
            )
            return state

    scheduled: list[Future[Any]] = []
    for event_id in event_ids_to_send:
        future = _schedule_outbox_event(
            context=context,
            run_id=run_id,
            report_dir=report_dir,
            rows_by_key=rows_by_key,
            event_id=event_id,
        )
        if future is not None:
            scheduled.append(future)
    if wait_for_completion:
        for future in scheduled:
            try:
                future.result()
            except Exception:
                logger.opt(exception=True).warning("outbox_sync_worker_failed", run_id=run_id)

    with context._lock:
        state = _load_state(build_dir)
        return state


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _value_by_path(root: dict[str, Any], dotted_path: str) -> Any:
    current: Any = root
    for token in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(token)
    return current


def _resolve_report_image(report_dir: Path, raw_path: str) -> Path | None:
    src = str(raw_path or "").strip()
    if not src:
        return None
    candidate = Path(src)
    if not candidate.is_absolute():
        candidate = (report_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(report_dir)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _resolve_baseline_image(context: ReportServerContext, report_dir: Path, row: dict[str, Any]) -> Path | None:
    direct = _resolve_report_image(report_dir, str(row.get("baseline_path", "")))
    if direct is not None:
        return direct
    suite_id = str(row.get("suite_id", "") or "").strip()
    scenario_id = str(row.get("scenario_id", "") or "").strip()
    viewport = str(row.get("viewport", "") or "").strip()
    browser = str(row.get("browser", "") or "").strip()
    if not (suite_id and scenario_id and viewport and browser):
        return None
    candidate = context.baseline_store.resolve_baseline(suite_id, scenario_id, viewport, browser)
    if candidate is None or not candidate.is_file():
        return None
    return candidate


def _build_reporting_payload(
    run_id: str,
    tag: str,
    row: dict[str, Any],
    case_state: dict[str, Any],
    event_type: str = "visual_report",
    event_note: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    metadata = _as_dict(row.get("test_metadata"))
    run_meta = _as_dict(metadata.get("run"))
    scenario_meta = _as_dict(metadata.get("scenario"))
    note_source = ""
    if tag == "BUG":
        note_source = _as_dict(case_state.get("bug")).get("note", "")
    elif tag == "ASO":
        note_source = _as_dict(case_state.get("aso")).get("note", "")
    note_text = str(note_source or "").strip()
    payload: dict[str, Any] = {
        "event_type": event_type,
        "run_id": run_id,
        "tag": tag,
        "scenario_id": str(row.get("scenario_id", "") or ""),
        "suite_id": str(row.get("suite_id", "") or scenario_meta.get("suite_id", "")),
        "viewport": str(row.get("viewport", "") or scenario_meta.get("viewport", "")),
        "browser": str(row.get("browser", "") or scenario_meta.get("browser", "")),
        "status": str(row.get("status", "") or ""),
        "message": str(row.get("message", "") or ""),
        "note": note_text,
        "metadata": metadata,
        "artifacts": {
            "baseline_path": str(row.get("baseline_path", "") or ""),
            "actual_path": str(row.get("actual_path", "") or ""),
            "diff_path": str(row.get("diff_path", "") or ""),
            "heatmap_path": str(row.get("heatmap_path", "") or ""),
        },
        "run": {
            "tester": str(run_meta.get("tester", row.get("tester", "")) or ""),
            "run_note": str(run_meta.get("run_note", row.get("run_note", "")) or ""),
        },
    }
    if event_note:
        payload["prompt_note"] = event_note
    if event_id:
        payload["idempotency_key"] = event_id
    return payload


def _draw_image_on_page(pdf: Any, image_path: Path, x: float, y: float, w: float, h: float) -> bool:
    if not _REPORTLAB_AVAILABLE or ImageReader is None:
        return False
    try:
        reader = ImageReader(str(image_path))
        img_w, img_h = reader.getSize()
        if img_w <= 0 or img_h <= 0:
            return False
        scale = min(w / float(img_w), h / float(img_h))
        draw_w = float(img_w) * scale
        draw_h = float(img_h) * scale
        draw_x = x + (w - draw_w) / 2.0
        draw_y = y + (h - draw_h) / 2.0
        pdf.drawImage(reader, draw_x, draw_y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
        return True
    except Exception:
        logger.opt(exception=True).warning("unable to draw image on pdf", image=str(image_path))
        return False


def _generate_bug_pdf(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    bug_rows: list[tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[str, int]:
    if not bug_rows:
        return "", 0
    if not _REPORTLAB_AVAILABLE or canvas is None or _r_pagesizes is None:
        logger.warning("reportlab not available; BUG pdf was skipped", run_id=run_id)
        return "", 0

    config = _load_bug_pdf_config(context.bug_pdf_config_path)
    page_w, page_h = _r_pagesizes.landscape(_r_pagesizes.A4)
    output = report_dir / f"{run_id}.pdf"
    pdf = canvas.Canvas(str(output), pagesize=(page_w, page_h))

    raw_fields = config.get("fields")
    fields: list[Any] = raw_fields if isinstance(raw_fields, list) else []
    raw_images = config.get("images")
    image_defs: list[Any] = raw_images if isinstance(raw_images, list) else []

    for row, case_state in bug_rows:
        metadata = _as_dict(row.get("test_metadata"))
        run_meta = _as_dict(metadata.get("run"))
        scenario_meta = _as_dict(metadata.get("scenario"))
        bug_state = _as_dict(case_state.get("bug"))
        aso_state = _as_dict(case_state.get("aso"))
        source = {
            "run": {
                "run_id": run_id,
                "tester": str(run_meta.get("tester", row.get("tester", "")) or ""),
                "run_note": str(run_meta.get("run_note", row.get("run_note", "")) or ""),
            },
            "scenario": {
                "name": str(scenario_meta.get("name", row.get("scenario_id", "")) or ""),
                "suite_id": str(scenario_meta.get("suite_id", row.get("suite_id", "")) or ""),
                "target_url": str(scenario_meta.get("target_url", row.get("target_url", "")) or ""),
                "viewport": str(scenario_meta.get("viewport", row.get("viewport", "")) or ""),
                "browser": str(scenario_meta.get("browser", row.get("browser", "")) or ""),
                "capture": _as_dict(scenario_meta.get("capture")),
            },
            "bug": {
                "note": str(bug_state.get("note", "") or "").strip(),
            },
            "aso": {
                "note": str(aso_state.get("note", "") or "").strip(),
            },
        }

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(24, page_h - 28, f"BUG report | run={run_id} | scenario={row.get('scenario_id', '')}")
        y = page_h - 52
        pdf.setFont("Helvetica", 9)
        for field_def in fields:
            if not isinstance(field_def, dict):
                continue
            path = str(field_def.get("path", "") or "").strip()
            label = str(field_def.get("label", path) or path)
            required = bool(field_def.get("required", False))
            if not path:
                continue
            value = _value_by_path(source, path)
            text = str(value if value is not None else "").strip()
            if not text and not required:
                continue
            if not text and required:
                text = "(missing)"
            pdf.drawString(24, y, f"{label}: {text}")
            y -= 12
            if y < page_h * 0.55:
                break

        image_top = page_h * 0.52
        image_bottom = 30
        image_height = image_top - image_bottom
        col_gap = 12
        col_width = (page_w - 24 * 2 - col_gap) / 2.0
        row_height = (image_height - col_gap) / 2.0

        grid = [
            (24, image_bottom + row_height + col_gap),
            (24 + col_width + col_gap, image_bottom + row_height + col_gap),
            (24, image_bottom),
            (24 + col_width + col_gap, image_bottom),
        ]

        image_source = {
            "image": {
                "baseline": str(row.get("baseline_path", "") or ""),
                "actual": str(row.get("actual_path", "") or ""),
                "diff": str(row.get("diff_path", "") or ""),
                "heatmap": str(row.get("heatmap_path", "") or ""),
            }
        }
        baseline_resolved = _resolve_baseline_image(context, report_dir, row)

        for idx, image_def in enumerate(image_defs[:4]):
            if not isinstance(image_def, dict):
                continue
            label = str(image_def.get("label", "image") or "image")
            path = str(image_def.get("path", "") or "").strip()
            gx, gy = grid[idx]
            pdf.rect(gx, gy, col_width, row_height)
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(gx + 4, gy + row_height - 11, label.upper())
            candidate: Path | None = None
            if path == "image.baseline" and baseline_resolved is not None:
                candidate = baseline_resolved
            elif path:
                raw = _value_by_path(image_source, path)
                candidate = _resolve_report_image(report_dir, str(raw or ""))
            if candidate is not None:
                _draw_image_on_page(pdf, candidate, gx + 4, gy + 4, col_width - 8, row_height - 18)
            else:
                pdf.setFont("Helvetica", 8)
                pdf.drawString(gx + 6, gy + 8, "image unavailable")

        pdf.showPage()

    pdf.save()
    logger.info("bug_pdf_generated", run_id=run_id, pages=len(bug_rows), path=str(output))
    return str(output), len(bug_rows)


def _build_handler(context: ReportServerContext):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, format, *args):
            pass

        def handle(self):
            try:
                super().handle()
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                pass

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = _json_bytes(payload)
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
                logger.debug(f"Client disconnected before response sent: {e}")
                return

        def _read_json_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            if content_length <= 0:
                return {}
            try:
                raw = self.rfile.read(content_length)
            except ConnectionResetError as exc:
                raise ValueError("client disconnected") from exc
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("request body must be a JSON object")
            return data

        def _serve_ui_index(self) -> None:
            _serve_file(self, context.ui_dist_dir / "index.html")

        def _serve_ui_asset(self, path: str) -> None:
            rel = path.lstrip("/")
            candidate = (context.ui_dist_dir / rel).resolve()
            try:
                candidate.relative_to(context.ui_dist_dir)
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN, "forbidden")
                return
            _serve_file(self, candidate)

        def _serve_report_file(self, run_id: str, rel_path: str) -> None:
            run_dir = context.resolve_run_dir(run_id)
            if run_dir is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                return

            clean_rel = rel_path.lstrip("/")
            candidate = (run_dir / clean_rel).resolve()
            try:
                candidate.relative_to(run_dir)
            except ValueError:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "path outside report directory"})
                return

            if not candidate.exists() and clean_rel.startswith("assets/"):
                self._serve_ui_asset(f"/{clean_rel}")
                return
            _serve_file(self, candidate)

        def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> bool:
            if path == "/api/app-info":
                self._send_json(HTTPStatus.OK, _build_app_info_payload(context))
                return True

            if path == "/api/perceptual/queue":
                self._send_json(HTTPStatus.OK, _perceptual_queue_payload(context))
                return True

            if path == "/api/perceptual/health":
                self._send_json(HTTPStatus.OK, _perceptual_health_payload(context))
                return True

            m_state = re.match(r"^/api/builds/([^/]+)/state$", path)
            if m_state:
                try:
                    run_id = _safe_run_id_or_error(m_state.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return True
                report_dir = context.resolve_run_dir(run_id)
                if report_dir is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return True
                build_dir = report_dir.parent
                with context._lock:
                    state = _load_state(build_dir)
                    if not context.reporting_enabled:
                        synced_cases, sent_events = _treat_reporting_disabled_as_success(state)
                        if synced_cases > 0 or sent_events > 0:
                            _save_state(build_dir, state)
                self._send_json(HTTPStatus.OK, {"run_id": run_id, "state": state})
                return True

            if path == "/api/reports":
                self._send_json(HTTPStatus.OK, {"reports": _list_reports_payload(context)})
                return True

            m_results = re.match(r"^/api/reports/([^/]+)/results$", path)
            if m_results:
                try:
                    run_id = _safe_run_id_or_error(m_results.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return True
                run_dir = context.resolve_run_dir(run_id)
                if run_dir is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return True
                rows = _read_results_rows(run_dir)
                run_metadata = _read_run_metadata(run_dir)
                tester = run_metadata.get("tester", "")
                run_note = run_metadata.get("run_note", "")
                enriched_rows: list[dict[str, Any]] = []
                for row in rows:
                    enriched = dict(row)
                    enriched.setdefault("tester", tester)
                    enriched.setdefault("run_note", run_note)
                    row_meta = enriched.get("test_metadata")
                    if not isinstance(row_meta, dict):
                        row_meta = {}
                    run_meta = row_meta.get("run")
                    if not isinstance(run_meta, dict):
                        run_meta = {}
                    run_meta.setdefault("run_id", run_id)
                    run_meta.setdefault("tester", tester)
                    run_meta.setdefault("run_note", run_note)
                    row_meta["run"] = run_meta
                    enriched["test_metadata"] = row_meta
                    enriched_rows.append(enriched)
                self._send_json(HTTPStatus.OK, {"run_id": run_id, "results": enriched_rows})
                return True

            m_ref = re.match(r"^/api/reports/([^/]+)/image/ref$", path)
            if m_ref:
                try:
                    run_id = _safe_run_id_or_error(m_ref.group(1))
                    if context.resolve_run_dir(run_id) is None:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                        return True

                    suite_id = (query.get("suite_id") or [""])[0].strip()
                    scenario_id = (query.get("scenario_id") or [""])[0].strip()
                    viewport = (query.get("viewport") or [""])[0].strip()
                    browser = (query.get("browser") or [""])[0].strip()
                    if not suite_id or not scenario_id or not viewport or not browser:
                        self._send_json(
                            HTTPStatus.BAD_REQUEST,
                            {"error": "missing required query params: suite_id, scenario_id, viewport, browser"},
                        )
                        return True

                    ref_path = context.baseline_store.resolve_baseline(suite_id, scenario_id, viewport, browser)
                    if ref_path is None or not ref_path.is_file():
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "baseline not found"})
                        return True
                    _serve_file(self, ref_path)
                    return True
                except Exception as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return True

            return False

        def do_GET(self) -> None:
            try:
                parsed = urlparse(self.path)
                path = parsed.path
                query = parse_qs(parsed.query)

                if path == "/health":
                    self._send_json(HTTPStatus.OK, {"status": "ok"})
                    return

                if path.startswith("/api/"):
                    handled = self._handle_api_get(path, query)
                    if handled:
                        return
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
                    return

                if path == "/" or path == "/index.html":
                    self._serve_ui_index()
                    return

                if path.startswith("/assets/"):
                    self._serve_ui_asset(path)
                    return

                m_report = re.match(r"^/reports/([^/]+)(?:/(.*))?$", path)
                if m_report:
                    try:
                        run_id = _safe_run_id_or_error(m_report.group(1))
                    except ValueError as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return
                    rel_path = (m_report.group(2) or "").strip()
                    if rel_path in {"", "index.html"}:
                        self._serve_ui_index()
                        return
                    self._serve_report_file(run_id, rel_path)
                    return

                self.send_error(HTTPStatus.NOT_FOUND, "not found")
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return
            except Exception:
                logger.opt(exception=True).warning("report server GET failed", path=self.path)
                try:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal server error"})
                except Exception:
                    return

        def do_PUT(self) -> None:
            path = urlparse(self.path).path
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})

        def do_POST(self) -> None:
            try:
                path = urlparse(self.path).path

                m_challenge = re.match(r"^/api/reports/([^/]+)/baseline/challenge$", path)
                if m_challenge:
                    try:
                        run_id = _safe_run_id_or_error(m_challenge.group(1))
                    except ValueError as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return
                    if context.resolve_run_dir(run_id) is None:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                        return

                    _cleanup_expired_challenges(context)
                    challenge_id = token_urlsafe(12)
                    phrase = _generate_phrase()
                    expires_at = time.time() + CHALLENGE_TTL_SECONDS
                    with context._lock:
                        context.challenges[challenge_id] = ChallengeEntry(
                            run_id=run_id, phrase=phrase, expires_at=expires_at
                        )
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "challenge_id": challenge_id,
                            "phrase": phrase,
                            "expires_at": int(expires_at),
                        },
                    )
                    return

                m_lock_acquire = re.match(r"^/(?:api/)?builds/([^/]+)/lock/acquire$", path)
                if m_lock_acquire:
                    try:
                        run_id = _safe_run_id_or_error(m_lock_acquire.group(1))
                        build_dir = _build_dir(context.repo_root, run_id)
                        payload = self._read_json_body()
                        client_id = _validated_text(payload.get("client_id"), "client_id")
                    except FileNotFoundError:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "build not found"})
                        return
                    except Exception as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return

                    with context._lock:
                        result = _acquire_lock(build_dir, client_id)
                    status = HTTPStatus.OK if result.get("accepted") else HTTPStatus.CONFLICT
                    self._send_json(status, result)
                    return

                m_lock_heartbeat = re.match(r"^/(?:api/)?builds/([^/]+)/lock/heartbeat$", path)
                if m_lock_heartbeat:
                    try:
                        run_id = _safe_run_id_or_error(m_lock_heartbeat.group(1))
                        build_dir = _build_dir(context.repo_root, run_id)
                        payload = self._read_json_body()
                        client_id = _validated_text(payload.get("client_id"), "client_id")
                        lock_id = _validated_text(payload.get("lock_id"), "lock_id")
                    except FileNotFoundError:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "build not found"})
                        return
                    except Exception as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return

                    with context._lock:
                        result = _heartbeat_lock(build_dir, client_id, lock_id)
                    status = HTTPStatus.OK if result.get("accepted") else HTTPStatus.CONFLICT
                    self._send_json(status, result)
                    return

                m_lock_release = re.match(r"^/(?:api/)?builds/([^/]+)/lock/release$", path)
                if m_lock_release:
                    try:
                        run_id = _safe_run_id_or_error(m_lock_release.group(1))
                        build_dir = _build_dir(context.repo_root, run_id)
                        payload = self._read_json_body()
                        client_id = _validated_text(payload.get("client_id"), "client_id")
                        lock_id = _validated_text(payload.get("lock_id"), "lock_id")
                    except FileNotFoundError:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "build not found"})
                        return
                    except Exception as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return

                    with context._lock:
                        result = _release_lock(build_dir, client_id, lock_id)
                    self._send_json(HTTPStatus.OK, result)
                    return

                m_events = re.match(r"^/(?:api/)?builds/([^/]+)/events$", path)
                if m_events:
                    try:
                        run_id = _safe_run_id_or_error(m_events.group(1))
                    except ValueError as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return

                    report_dir = context.resolve_run_dir(run_id)
                    if report_dir is None:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                        return

                    try:
                        payload = self._read_json_body()
                    except Exception as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid request body: {exc}"})
                        return

                    event_id = _normalize_text(payload.get("event_id"), trim=True)
                    event_type = str(payload.get("type", "")).strip().upper()
                    case_id = _normalize_text(payload.get("test_case_id"), trim=True)
                    event_payload = (
                        cast(dict[str, Any], payload.get("payload")) if isinstance(payload.get("payload"), dict) else {}
                    )

                    if not event_id:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": "missing event_id"})
                        return
                    if event_type not in {"BUG_SET", "ASO_SET"}:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid event type"})
                        return
                    if not case_id:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": "missing test_case_id"})
                        return

                    build_dir = report_dir.parent
                    reporting_enabled = False
                    event_id_to_send = ""
                    with context._lock:
                        state = _load_state(build_dir)
                        outbox = state.setdefault("outbox", [])
                        existing = next((item for item in outbox if item.get("event_id") == event_id), None)
                        if existing:
                            self._send_json(
                                HTTPStatus.OK,
                                {
                                    "accepted": True,
                                    "duplicate": True,
                                    "event": existing,
                                    "test_cases": state.get("test_cases", {}),
                                },
                            )
                            return

                        case_state = _ensure_case_state(state, case_id)
                        if event_type == "BUG_SET" and case_state["bug"]["locked"]:
                            self._send_json(HTTPStatus.CONFLICT, {"error": "BUG already locked"})
                            return
                        if event_type == "ASO_SET" and case_state["aso"]["locked"]:
                            self._send_json(HTTPStatus.CONFLICT, {"error": "ASO already locked"})
                            return

                        prompt_note = _normalize_text(event_payload.get("note"), trim=True)
                        if len(prompt_note) > TEXT_MAX_LENGTH:
                            self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": f"note exceeds {TEXT_MAX_LENGTH} characters"}
                            )
                            return

                        note_content = prompt_note

                        case_state = _apply_event_to_state(state, case_id, event_type, note_content)

                        event_payload_out: dict[str, Any] = {}
                        if prompt_note:
                            event_payload_out["note"] = prompt_note

                        event_entry = {
                            "event_id": event_id,
                            "type": event_type,
                            "payload": event_payload_out,
                            "status": "pending",
                            "attempts": 0,
                            "last_attempt_at": "",
                            "sent_at": "",
                            "last_error": "",
                            "test_case_id": case_id,
                        }
                        outbox.append(event_entry)

                        if not context.reporting_enabled:
                            _record_event_attempt(event_entry, True, "")
                            _mark_case_synced(case_state, event_type)

                        _save_state(build_dir, state)

                        reporting_enabled = bool(
                            context.reporting_enabled and context.reporting_client and context.reporting_client.enabled
                        )

                        if reporting_enabled:
                            event_id_to_send = str(event_entry.get("event_id", ""))

                    if not reporting_enabled:
                        logger.debug(
                            "reporting_api_disabled_skipping_sync",
                            run_id=run_id,
                            event_type=event_type,
                            case_id=case_id,
                        )
                    elif event_id_to_send:
                        rows = _read_results_rows(report_dir)
                        rows_by_key = {_row_tag_key(row): row for row in rows}
                        future = _schedule_outbox_event(
                            context=context,
                            run_id=run_id,
                            report_dir=report_dir,
                            rows_by_key=rows_by_key,
                            event_id=event_id_to_send,
                        )
                        if future is None:
                            logger.warning(
                                "reporting_sync_executor_unavailable",
                                run_id=run_id,
                                event_type=event_type,
                                case_id=case_id,
                            )

                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "accepted": True,
                            "event": event_entry,
                            "test_cases": state.get("test_cases", {}),
                        },
                    )
                    return

                m_report = re.match(r"^/(?:api/)?builds/([^/]+)/report$", path)
                if m_report:
                    try:
                        run_id = _safe_run_id_or_error(m_report.group(1))
                    except ValueError as exc:
                        self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                        return
                    report_dir = context.resolve_run_dir(run_id)
                    if report_dir is None:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                        return

                    state = _flush_pending(context, run_id, report_dir, wait_for_completion=False)
                    bug_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
                    for row in _read_results_rows(report_dir):
                        case_id = _row_tag_key(row)
                        case_state = state.get("test_cases", {}).get(case_id)
                        if not isinstance(case_state, dict):
                            continue
                        if case_state.get("bug", {}).get("locked"):
                            bug_rows.append((row, case_state))

                    pdf_path, pdf_pages = _generate_bug_pdf(
                        context=context,
                        run_id=run_id,
                        report_dir=report_dir,
                        bug_rows=bug_rows,
                    )

                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "accepted": True,
                            "run_id": run_id,
                            "pdf": {"path": pdf_path, "pages": pdf_pages},
                            "state": state,
                            "test_cases": state.get("test_cases", {}),
                        },
                    )
                    return

                m_send = re.match(r"^/api/reports/([^/]+)/baseline/send$", path)
                if not m_send:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
                    return

                try:
                    run_id = _safe_run_id_or_error(m_send.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                report_dir = context.resolve_run_dir(run_id)
                if report_dir is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return

                try:
                    payload = self._read_json_body()
                    challenge_id = _as_non_empty_text(payload, "challenge_id")
                    phrase = _as_non_empty_text(payload, "phrase")
                    items = payload.get("items")
                    if not isinstance(items, list):
                        raise ValueError("missing or invalid field: items")
                except Exception as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return

                _cleanup_expired_challenges(context)
                with context._lock:
                    challenge = context.challenges.get(challenge_id)
                    if challenge is None:
                        self._send_json(HTTPStatus.FORBIDDEN, {"error": "challenge is missing or expired"})
                        return
                    if challenge.phrase != phrase:
                        self._send_json(HTTPStatus.FORBIDDEN, {"error": "challenge phrase mismatch"})
                        return
                    if challenge.run_id != run_id:
                        self._send_json(HTTPStatus.FORBIDDEN, {"error": "challenge run mismatch"})
                        return

                    context.challenges.pop(challenge_id, None)

                results: list[dict[str, Any]] = []
                saved_count = 0
                failed_count = 0
                for raw_item in items:
                    if not isinstance(raw_item, dict):
                        failed_count += 1
                        results.append({"status": "failed", "message": "item must be an object"})
                        continue
                    try:
                        scenario_id = _as_non_empty_text(raw_item, "scenario_id")
                        suite_id = _as_non_empty_text(raw_item, "suite_id")
                        viewport = _as_non_empty_text(raw_item, "viewport")
                        browser = _as_non_empty_text(raw_item, "browser")
                        actual_path = _as_non_empty_text(raw_item, "actual_path")
                        source = _resolve_actual_png(report_dir, actual_path)
                        target = cast(Any, context.baseline_store).store_local_baseline(
                            suite_id,
                            scenario_id,
                            viewport,
                            browser,
                            source,
                            version_override="candidates",
                        )
                        results.append(
                            {
                                "status": "saved",
                                "scenario_id": scenario_id,
                                "source_path": str(source),
                                "target_path": str(target),
                            }
                        )
                        saved_count += 1
                    except Exception as exc:
                        failed_count += 1
                        results.append(
                            {
                                "status": "failed",
                                "scenario_id": str(raw_item.get("scenario_id", "")),
                                "message": str(exc),
                            }
                        )

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "accepted": failed_count == 0,
                        "saved_count": saved_count,
                        "failed_count": failed_count,
                        "results": results,
                    },
                )
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return
            except Exception:
                logger.opt(exception=True).warning("report server POST failed", path=self.path)
                try:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal server error"})
                except Exception:
                    return

    return Handler


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Serve visual reports with listing and baseline approval endpoints")
    parser.add_argument("--report-dir", default="", help="Path to visual report directory (artifacts/<run_id>/visual)")
    parser.add_argument("--run-id", default="", help="Run id under artifacts/<run_id>/visual")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    ui_dist_dir = (REPO_ROOT / "framework" / "visual" / "ui" / "dist").resolve()
    if not ui_dist_dir.is_dir():
        raise FileNotFoundError("UI build missing; run `npm run build` inside framework/visual/ui")

    run_dirs = _discover_visual_run_dirs(REPO_ROOT)
    selected_run_id = ""
    pinned_run_dirs: dict[str, Path] = {}
    if args.run_id or args.report_dir:
        selected_report_dir = _resolve_report_dir(REPO_ROOT, args.report_dir or None, args.run_id or None)
        selected_run_id = _run_id_from_visual_dir(REPO_ROOT, selected_report_dir)
        pinned_run_dirs[selected_run_id] = selected_report_dir

    env = load_env()
    reporting_enabled = bool(env.reporting_enabled)
    reporting_api_url = str(env.reporting_api_url or "").strip()
    sync_workers = _resolve_sync_workers(REPORT_SYNC_WORKERS)
    sync_executor = ThreadPoolExecutor(max_workers=sync_workers, thread_name_prefix="report-sync")
    reporting_client: ReportingClient | None = None
    if reporting_enabled:
        if not reporting_api_url:
            logger.error(
                "reporting_config_missing_url", message="reporting_enabled=true but REPORTING_API_URL is empty"
            )
            reporting_enabled = False
        else:
            reporting_client = ReportingClient(
                enabled=True,
                base_url=reporting_api_url,
                token=env.reporting_api_token,
                timeout_seconds=env.reporting_api_timeout_seconds,
                retries=env.reporting_api_retries,
            )
    context = ReportServerContext(
        repo_root=REPO_ROOT,
        ui_dist_dir=ui_dist_dir,
        baseline_store=BaselineStore(env, REPO_ROOT),
        run_dirs=run_dirs,
        pinned_run_dirs=pinned_run_dirs,
        reporting_client=reporting_client,
        reporting_enabled=reporting_enabled,
        reporting_bug_endpoint=str(cast(Any, env).reporting_api_bug_endpoint or "").strip(),
        reporting_aso_endpoint=str(cast(Any, env).reporting_api_aso_endpoint or "").strip(),
        sync_workers=sync_workers,
        sync_executor=sync_executor,
        pms_enabled=bool(env.pms_enabled),
        pms_base_url=str(env.pms_base_url or "").strip(),
        pms_timeout_sec=int(env.pms_timeout_sec),
        pms_health_timeout_seconds=int(env.pms_health_timeout_seconds),
        pms_retry_max=int(env.pms_retry_max),
        bug_pdf_config_path=(
            REPO_ROOT / "framework" / "visual" / "ui" / "src" / "config" / "bug_report_pdf_config.json"
        ),
    )
    handler = _build_handler(context)
    server = ThreadingHTTPServer((args.host, int(args.port)), handler)

    print(f"ui dist dir: {ui_dist_dir}")
    if selected_run_id:
        print(f"selected report: {selected_run_id} -> {pinned_run_dirs.get(selected_run_id)}")
        print(f"server listening: http://{args.host}:{args.port}/reports/{selected_run_id}")
    else:
        print(f"server listening: http://{args.host}:{args.port}/")
    print(f"report sync workers: {sync_workers}")
    print(
        "endpoints: GET /api/app-info, GET /api/perceptual/queue, GET /api/perceptual/health, GET /api/reports, "
        "GET /api/reports/<run_id>/results, GET /api/reports/<run_id>/image/ref"
    )
    print(
        "endpoints: GET /api/builds/<run_id>/state, "
        "POST /api/builds/<run_id>/events, "
        "POST /api/builds/<run_id>/lock/acquire, "
        "POST /api/builds/<run_id>/lock/heartbeat, "
        "POST /api/builds/<run_id>/lock/release, "
        "POST /api/builds/<run_id>/report, "
        "POST /api/reports/<run_id>/baseline/challenge, "
        "POST /api/reports/<run_id>/baseline/send"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down report server")
    finally:
        server.server_close()
        sync_executor.shutdown(wait=False, cancel_futures=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
