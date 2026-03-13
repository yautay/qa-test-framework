from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from framework.visual.models import VisualResult


_REPORT_FILE = "build-metadata.json"
_FIXTURE_REQUEST_RE = re.compile(r"^request\s*=\s*<FixtureRequest", re.IGNORECASE)


def _normalize_reason_text(message: str) -> str:
    lines = [str(line or "").strip() for line in str(message or "").splitlines()]
    filtered = [line for line in lines if line and not _FIXTURE_REQUEST_RE.match(line)]
    if not filtered:
        return ""
    compact = " | ".join(filtered)
    return compact[:500]


def _classify_exclusion_reason(*, phase: str, status: str, message: str) -> tuple[str, str, str, str]:
    raw = str(message or "").strip()[:1000]
    normalized = _normalize_reason_text(raw)
    source = normalized or raw
    lower = source.lower()
    phase_token = str(phase or "").strip().lower()
    status_token = str(status or "").strip().lower()

    if "timeout" in lower or "timed out" in lower:
        title = "Timeout during test execution"
        details = normalized or "Pytest timeout before visual result was produced"
        return "timeout", title, details, raw

    if "assertionerror" in lower or "assert " in lower:
        title = "Assertion failed before visual capture"
        details = normalized or "Assertion failed before visual result was produced"
        return "assertion_error", title, details, raw

    if "collect" in lower:
        title = "Test collection error"
        details = normalized or "Pytest collection failed before visual result was produced"
        return "collection_error", title, details, raw

    if phase_token == "teardown":
        title = "Fixture teardown error"
        details = normalized or "Fixture teardown failed before visual result was produced"
        return "fixture_teardown_error", title, details, raw

    if phase_token == "setup" or "fixture" in lower:
        title = "Fixture setup error"
        details = normalized or "Fixture setup failed before visual result was produced"
        return "fixture_setup_error", title, details, raw

    if status_token == "failed":
        title = "Test failed before visual capture"
        details = normalized or "Pytest failed before visual result was produced"
        return "test_failed", title, details, raw

    if status_token == "error":
        title = "Pytest execution error"
        details = normalized or "Pytest error before visual result was produced"
        return "execution_error", title, details, raw

    title = "Unknown exclusion reason"
    details = normalized or f"pytest status={status_token or 'unknown'} before visual result was produced"
    return "unknown", title, details, raw


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
        longrepr = str(pytest_outcome.get("longrepr", "") or "").strip()
        message = str(pytest_outcome.get("message", "") or "").strip()
        reason = longrepr or message
        if reason:
            return phase, reason[:5000]
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
    reason_counter: Counter[tuple[str, str]] = Counter()
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
        reason_code, reason_title, reason_details, reason_raw = _classify_exclusion_reason(
            phase=phase,
            status=status,
            message=reason,
        )
        reason_counter[(reason_code, reason_title)] += 1
        excluded_cases.append(
            {
                "nodeid": normalized_nodeid,
                "status": status,
                "phase": phase,
                "reason": reason_details,
                "reason_code": reason_code,
                "reason_title": reason_title,
                "reason_details": reason_details,
                "reason_raw": reason_raw,
            }
        )

    excluded_cases.sort(key=lambda row: row.get("nodeid", ""))
    excluded_reasons_summary = [
        {
            "reason_code": reason_code,
            "reason_title": reason_title,
            "count": int(count),
        }
        for (reason_code, reason_title), count in sorted(
            reason_counter.items(),
            key=lambda item: (-item[1], item[0][1]),
        )
    ]
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "visual": {
            "collected_count": int(collected_visual_count),
            "included_count": int(len(included_nodeids)),
            "excluded_count": int(len(excluded_cases)),
            "excluded_cases": excluded_cases,
            "excluded_reasons_summary": excluded_reasons_summary,
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
