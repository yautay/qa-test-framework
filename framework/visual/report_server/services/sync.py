from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
from typing import Any, cast

from loguru import logger

from ..context import ReportServerContext
from ..reports import _read_results_rows
from ..state import (
    _ensure_case_state,
    _load_state,
    _normalize_text,
    _record_event_attempt,
    _save_state,
    _treat_reporting_disabled_as_success,
)


def _row_tag_key(row: dict[str, Any]) -> str:
    return "::".join(
        [
            str(row.get("scenario_id", "") or ""),
            str(row.get("actual_path", "") or ""),
            str(row.get("baseline_path", "") or ""),
            str(row.get("diff_path", "") or ""),
        ]
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def _mark_case_synced(case_state: dict[str, Any], event_type: str) -> None:
    if event_type == "BUG_SET":
        case_state["bug"]["synced"] = True
    elif event_type == "ASO_SET":
        case_state["aso"]["synced"] = True


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
    req = _build_reporting_payload(
        run_id,
        tag,
        row,
        case_state,
        event_type="visual_report",
        event_note=payload_note,
        event_id=str(event.get("event_id", "")) or None,
    )
    accepted = bool(cast(Any, context.reporting_client).send_payload(endpoint, req))
    if accepted:
        return True, ""
    return False, "api rejected"


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
        return _load_state(build_dir)
