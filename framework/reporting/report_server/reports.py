from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .context import ReportServerContext
from .state import _load_state, _save_state, _treat_reporting_disabled_as_success
from framework.visual.build_metadata import read_visual_build_metadata

_PERCEPTUAL_STATUS = "perceptual-status.json"


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


def _read_build_metadata(report_dir: Path) -> dict[str, Any]:
    payload = read_visual_build_metadata(report_dir)
    return payload if isinstance(payload, dict) else {}


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
