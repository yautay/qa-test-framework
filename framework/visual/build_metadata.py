from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from framework.visual.models import VisualResult


_REPORT_FILE = "build-metadata.json"


def _is_visual_payload(nodeid: str, payload: dict[str, Any]) -> bool:
    token = str(nodeid or "").strip().replace("\\", "/")
    if token.startswith("qa/visual/") or "/qa/visual/" in token:
        return True
    markers = payload.get("markers")
    if not isinstance(markers, list):
        return False
    marker_names = {str(item or "").strip().lower() for item in markers}
    return "visual" in marker_names


def _as_reason(payload: dict[str, Any], status: str) -> tuple[str, str]:
    pytest_outcome = payload.get("pytest_outcome")
    if isinstance(pytest_outcome, dict):
        phase = str(pytest_outcome.get("phase", "") or "")
        message = str(pytest_outcome.get("message", "") or "").strip()
        if message:
            return phase, message[:300]
    timing = payload.get("timing")
    if isinstance(timing, dict) and status == "skipped":
        return "call", "pytest skipped before visual result was produced"
    return "", f"pytest status={status} before visual result was produced"


def build_visual_build_metadata(
    *,
    results: list[VisualResult],
    payloads_by_nodeid: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    included_nodeids = {
        str(getattr(result, "nodeid", "") or "").strip()
        for result in results
        if str(getattr(result, "nodeid", "") or "").strip()
    }
    excluded_cases: list[dict[str, str]] = []
    collected_visual_count = 0
    for nodeid, payload in payloads_by_nodeid.items():
        if not isinstance(payload, dict):
            continue
        normalized_nodeid = str(nodeid or "").strip()
        if not normalized_nodeid:
            continue
        if not _is_visual_payload(normalized_nodeid, payload):
            continue
        collected_visual_count += 1
        if normalized_nodeid in included_nodeids:
            continue
        status = str(payload.get("status", "") or "").strip().lower()
        if status not in {"error", "failed"}:
            continue
        phase, reason = _as_reason(payload, status)
        excluded_cases.append(
            {
                "nodeid": normalized_nodeid,
                "status": status,
                "phase": phase,
                "reason": reason,
            }
        )

    excluded_cases.sort(key=lambda row: row.get("nodeid", ""))
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "visual": {
            "collected_count": int(collected_visual_count),
            "included_count": int(len(included_nodeids)),
            "excluded_count": int(len(excluded_cases)),
            "excluded_cases": excluded_cases,
        },
    }


def write_visual_build_metadata(report_dir: Path, metadata: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    target = report_dir / _REPORT_FILE
    temp = report_dir / f"{_REPORT_FILE}.tmp"
    temp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)


def read_visual_build_metadata(report_dir: Path) -> dict[str, Any]:
    target = report_dir / _REPORT_FILE
    if not target.is_file():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload
