from __future__ import annotations

import tempfile
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from zoneinfo import ZoneInfo

from framework.integrations.jira import JiraAuth, JiraClient, JiraClientError

from ..context import ReportServerContext
from ..reports import _read_results_rows
from ..services.pdf import _load_bug_pdf_config
from ..services.sync import _row_tag_key
from ..state import _load_state

try:
    import cv2  # type: ignore[import]
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None


def _ascii_safe(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if ord(ch) < 128)


def _value_by_path(source: dict[str, Any], path: str) -> str:
    current: Any = source
    for token in path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(token) if isinstance(current, dict) else None
    return str(current or "")


def _build_metadata_source(row: dict[str, Any], case_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata = row.get("test_metadata") if isinstance(row.get("test_metadata"), dict) else {}
    run_meta = metadata.get("run") if isinstance(metadata.get("run"), dict) else {}
    scenario_meta = metadata.get("scenario") if isinstance(metadata.get("scenario"), dict) else {}
    return {
        "run": {
            "tester": str(run_meta.get("tester", row.get("tester", "")) or ""),
            "run_note": str(run_meta.get("run_note", row.get("run_note", "")) or ""),
        },
        "scenario": {
            "name": str(scenario_meta.get("name", row.get("scenario_id", "")) or ""),
            "suite_id": str(scenario_meta.get("suite_id", row.get("suite_id", "")) or ""),
            "target_url": str(scenario_meta.get("target_url", row.get("target_url", "")) or ""),
            "viewport": str(scenario_meta.get("viewport", row.get("viewport", "")) or ""),
            "browser": str(scenario_meta.get("browser", row.get("browser", "")) or ""),
            "capture": scenario_meta.get("capture", {}) if isinstance(scenario_meta.get("capture"), dict) else {},
        },
        "bug": {
            "note": str(case_state.get("bug", {}).get("note", "") or ""),
        },
        "aso": {
            "note": str(case_state.get("aso", {}).get("note", "") or ""),
        },
    }


def _build_badge_line(bug_count: int, aso_count: int) -> list[str]:
    badges = []
    if bug_count:
        badges.append("visual-regression: Failed (green)")
    else:
        badges.append("visual-regression: Passed (red)")
    if aso_count:
        badges.append("visual-regression-aso: Attention! (yellow)")
    return badges


def _prepare_attachment(
    diff_path: Path,
    max_width: int,
    scratch_dir: Path,
) -> Path | None:
    if not diff_path.is_file():
        return None
    if cv2 is None:
        return diff_path
    image = cv2.imread(str(diff_path))
    if image is None:
        return diff_path
    height, width = image.shape[:2]
    if width <= 0 or max_width <= 0:
        return diff_path
    if width <= max_width:
        return diff_path
    ratio = float(max_width) / float(width)
    new_height = max(1, int(round(height * ratio)))
    resized = cv2.resize(image, (max(1, int(round(max_width))), new_height), interpolation=cv2.INTER_AREA)
    target = scratch_dir / f"{diff_path.stem}-scaled{diff_path.suffix or '.png'}"
    cv2.imwrite(str(target), resized)
    return target


def _build_client(context: ReportServerContext, auth: dict[str, str] | None) -> JiraClient:
    if auth:
        username = str(auth.get("username", "")).strip()
        password = str(auth.get("password", "")).strip()
        api_token = str(auth.get("api_token", "")).strip()
        mode = str(auth.get("mode", context.jira_auth_mode or "basic")).strip().lower()
        credentials = None
        if mode == "token" and username and api_token:
            credentials = JiraAuth(mode="token", username=username, password="", api_token=api_token)
        elif username and password:
            credentials = JiraAuth(mode="basic", username=username, password=password, api_token=api_token)
        if credentials:
            return JiraClient(
                base_url=context.jira_url,
                verify_ssl=context.jira_verify_ssl,
                auth=credentials,
            )
        raise JiraClientError("jira credentials invalid", status=None)
    if context.jira_client:
        return context.jira_client
    raise JiraClientError("jira integration is not configured", status=None)


def _run_base_url(host: str, scheme: str) -> str:
    if not host:
        return ""
    proto = scheme.lower() if scheme else "http"
    host_str = host.strip()
    if not host_str:
        return ""
    return f"{proto}://{host_str}"


def _log_attempt(
    level: str,
    issue_key: str,
    run_id: str,
    attempt: int,
    status: int | None,
    message: str,
) -> None:
    context = {
        "issue_key": issue_key,
        "run_id": run_id,
        "attempt": attempt,
        "status_code_class": f"{status // 100}xx" if status else "unknown",
    }
    logger.log(level, message, **context)


def _with_retries(
    *,
    attempts: int,
    action: str,
    issue_key: str,
    run_id: str,
    fn,
) -> Any:
    last_error: JiraClientError | None = None
    for attempt in range(1, attempts + 1):
        try:
            result = fn()
            _log_attempt("INFO", issue_key, run_id, attempt, None, f"jira_{action}_success")
            return result
        except JiraClientError as exc:
            last_error = exc
            if attempt < attempts:
                _log_attempt("WARNING", issue_key, run_id, attempt, exc.status, f"jira_{action}_retry")
                time.sleep(1)
                continue
            status = exc.status
            _log_attempt("ERROR", issue_key, run_id, attempt, status, f"jira_{action}_failed")
            raise
    raise last_error or JiraClientError("jira operation failed", status=None)


def send_jira_comment(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    issue_key: str,
    user_note: str,
    auth: dict[str, str] | None,
    scheme: str,
    host: str,
) -> dict[str, Any]:
    client = _build_client(context, auth)
    rows = _read_results_rows(report_dir)
    state = _load_state(report_dir.parent)
    rows_by_key = {_row_tag_key(row): row for row in rows}
    bugs = []
    asos = []
    for case_id, case_state in state.get("test_cases", {}).items():
        if not isinstance(case_state, dict):
            continue
        if case_state.get("bug", {}).get("locked"):
            bugs.append(case_id)
        if case_state.get("aso", {}).get("locked"):
            asos.append(case_id)
    bug_count = len(bugs)
    aso_count = len(asos)
    base_url = _run_base_url(host, scheme)
    report_url = f"{base_url}/reports/{run_id}" if base_url else f"/reports/{run_id}"
    timestamp = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M:%S %Z")
    badge_lines = _build_badge_line(bug_count, aso_count)
    lines = [*badge_lines, f"Timestamp: {timestamp}"]
    if user_note:
        lines.append(f"User note: {user_note}")
    bug_section = []
    attachments: list[Path] = []
    fields = _load_bug_pdf_config(context.bug_pdf_config_path).get("fields", [])
    with tempfile.TemporaryDirectory() as scratch:
        scratch_path = Path(scratch)
        for case_id in bugs:
            row = rows_by_key.get(case_id)
            if row is None:
                continue
            case_state = state.get("test_cases", {}).get(case_id, {})
            source = _build_metadata_source(row, case_state)
            field_lines: list[str] = []
            for field in fields:
                if not isinstance(field, dict):
                    continue
                label = str(field.get("label", ""))
                path = str(field.get("path", ""))
                if not path or not label:
                    continue
                value = _value_by_path(source, path)
                if value:
                    field_lines.append(f"  - {label}: {value}")
            diff_rel = str(row.get("diff_path", ""))
            missing_note = None
            if diff_rel:
                diff_file = (report_dir / diff_rel).resolve(strict=False)
                scaled = _prepare_attachment(diff_file, context.jira_pixel_diff_max_width_px, scratch_path)
                if scaled and scaled.is_file():
                    attachments.append(scaled)
                else:
                    missing_note = f"{row.get('scenario_id', 'unknown')} ({diff_rel})"
            else:
                missing_note = f"{row.get('scenario_id', 'unknown')} (missing path)"
            bug_section.append(f"Scenario: {source['scenario'].get('name')}")
            bug_section.extend(field_lines)
            bug_section.append(f"  - Report link: {report_url}")
            if diff_rel:
                diff_url = (
                    f"{report_url}/{diff_rel}" if base_url else f"/reports/{run_id}/{diff_rel}".replace("//", "/")
                )
                bug_section.append(f"  - Diff: {diff_url}")
            if missing_note:
                bug_section.append(f"  - Diff missing: {missing_note}")
        if bug_section:
            lines.append("")
            lines.append("BUGS:")
            lines.extend(bug_section)
        if aso_count and asos:
            if bug_section:
                lines.append("---")
            lines.append("ASO requests:")
            mentions = " ".join(f"[~{name}]" for name in context.jira_aso_mentions if name)
            if mentions:
                lines.append(f"Mentions: {mentions}")
            for case_id in asos:
                row = rows_by_key.get(case_id)
                if not row:
                    continue
                target = _value_by_path(
                    _build_metadata_source(row, state.get("test_cases", {}).get(case_id, {})), "scenario.target_url"
                )
                aso_note = _ascii_safe(str(state.get("test_cases", {}).get(case_id, {}).get("aso", {}).get("note", "")))
                lines.append(f"- scenario: {row.get('scenario_id', 'unknown')} | target: {target}")
                if aso_note:
                    lines.append(f"  - ASO note: {aso_note}")
    comment_body = _ascii_safe("\n".join(lines))
    result = _with_retries(
        attempts=max(1, int(context.jira_retry_max)),
        action="add_comment",
        issue_key=issue_key,
        run_id=run_id,
        fn=lambda: client.add_comment(issue_key, comment_body),
    )
    for attachment in attachments:
        _with_retries(
            attempts=max(1, int(context.jira_retry_max)),
            action="add_attachment",
            issue_key=issue_key,
            run_id=run_id,
            fn=lambda path=attachment: client.add_attachment(issue_key, path),
        )
        time.sleep(max(0, float(context.jira_upload_delay_seconds)))
    return {
        "issue": issue_key,
        "run_id": run_id,
        "attachments": len(attachments),
        "result": result,
    }
