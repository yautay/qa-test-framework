from __future__ import annotations

import tempfile
import time
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

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


SUBTASK_SUMMARY_PATTERN = re.compile(r"^\[bug\] VRT #(\d+) - ")
ISSUE_KEY_PATTERN = re.compile(r"^([A-Z][A-Z0-9]+)-\d+$")
SUBTASK_MAX_ATTEMPTS = 8


def _jira_safe_text(text: str) -> str:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "".join(ch for ch in raw if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127))
    return cleaned.strip()


def _escape_table_cell(text: str) -> str:
    token = _jira_safe_text(text)
    if not token:
        return "-"
    return token.replace("|", "\\|").replace("\n", "<br/>")


def _format_jira_link(label: str, url: str) -> str:
    safe_label = _escape_table_cell(label)
    safe_url = _jira_safe_text(url)
    if not safe_url:
        return safe_label
    return f"[{safe_label}|{safe_url}]"


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
    execution_meta = metadata.get("execution") if isinstance(metadata.get("execution"), dict) else {}
    target_url = str(scenario_meta.get("target_url", row.get("target_url", "")) or "")
    target_base_url = str(execution_meta.get("target_base_url", "") or "")
    target_full_url = _build_target_full_url(target_base_url, target_url)
    return {
        "run": {
            "tester": str(run_meta.get("tester", row.get("tester", "")) or ""),
            "run_note": str(run_meta.get("run_note", row.get("run_note", "")) or ""),
        },
        "scenario": {
            "name": str(scenario_meta.get("name", row.get("scenario_id", "")) or ""),
            "suite_id": str(scenario_meta.get("suite_id", row.get("suite_id", "")) or ""),
            "target_url": target_url,
            "viewport": str(scenario_meta.get("viewport", row.get("viewport", "")) or ""),
            "browser": str(scenario_meta.get("browser", row.get("browser", "")) or ""),
            "capture": scenario_meta.get("capture", {}) if isinstance(scenario_meta.get("capture"), dict) else {},
        },
        "execution": {
            "target_base_url": target_base_url,
            "target_full_url": target_full_url,
        },
        "bug": {
            "note": str(case_state.get("bug", {}).get("note", "") or ""),
        },
        "aso": {
            "note": str(case_state.get("aso", {}).get("note", "") or ""),
        },
    }


def _build_badge_line(bug_count: int, aso_count: int) -> list[str]:
    badges = ["🔴 visual-regression: FAIL" if bug_count else "🟢 visual-regression: PASS"]
    if aso_count:
        badges.append("🟡 visual-regression-aso: ATTENTION")
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


def _build_target_full_url(base_url: str, target_url: str) -> str:
    endpoint = str(target_url or "").strip()
    if not endpoint:
        return ""
    lowered = endpoint.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return endpoint
    base = str(base_url or "").strip()
    if not base:
        return ""
    try:
        return urljoin(base.rstrip("/") + "/", endpoint)
    except Exception:
        return ""


def _normalize_framework_mode(value: str) -> str:
    token = str(value or "").strip().lower()
    if token == "local":
        return "local"
    return "server"


def _build_attachment_filename(*, idx: int, scenario: str, suffix: str) -> str:
    ext = str(suffix or ".png").strip()
    if not ext.startswith("."):
        ext = f".{ext}"
    safe_scenario = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(scenario or "")).strip("-") or "scenario"
    return f"bug-{max(1, int(idx)):03d}-{safe_scenario}{ext}"


def _extract_run_git_info(rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    out = {
        "frontend": {"branch": "", "commit": ""},
        "backend": {"branch": "", "commit": ""},
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        metadata = row.get("test_metadata") if isinstance(row.get("test_metadata"), dict) else {}
        run_meta = metadata.get("run") if isinstance(metadata.get("run"), dict) else {}
        target_git_info = run_meta.get("target_git_info") if isinstance(run_meta.get("target_git_info"), dict) else {}
        for target in ("frontend", "backend"):
            info = target_git_info.get(target) if isinstance(target_git_info.get(target), dict) else {}
            branch = str(info.get("branch", "") or "").strip()
            commit = str(info.get("commit", "") or "").strip()
            if branch:
                out[target]["branch"] = branch
            if commit:
                out[target]["commit"] = commit
    return out


def _resolve_browser_details(row: dict[str, Any], source: dict[str, dict[str, Any]]) -> str:
    metadata = row.get("test_metadata") if isinstance(row.get("test_metadata"), dict) else {}
    execution_meta = metadata.get("execution") if isinstance(metadata.get("execution"), dict) else {}
    browser = _jira_safe_text(str(source.get("scenario", {}).get("browser", "") or row.get("browser", "")))
    version = ""
    for key in ("browser_version", "browserVersion", "playwright_browser_version", "playwrightBrowserVersion"):
        token = _jira_safe_text(str(execution_meta.get(key, "") or row.get(key, "")))
        if token:
            version = token
            break
    user_agent = _jira_safe_text(str(execution_meta.get("user_agent", "") or execution_meta.get("userAgent", "")))
    if user_agent and len(user_agent) > 180:
        user_agent = f"{user_agent[:177]}..."
    chunks = []
    if browser:
        chunks.append(browser)
    if version:
        chunks.append(f"version={version}")
    if user_agent:
        chunks.append(f"ua={user_agent}")
    return " | ".join(chunks)


def _payload_to_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.strip()
    if not isinstance(payload, dict):
        return str(payload).strip()
    fragments: list[str] = []
    error_messages = payload.get("errorMessages")
    if isinstance(error_messages, list):
        items = [str(item).strip() for item in error_messages if str(item).strip()]
        if items:
            fragments.append("; ".join(items))
    errors = payload.get("errors")
    if isinstance(errors, dict):
        for key, value in errors.items():
            message = str(value or "").strip()
            if message:
                fragments.append(f"{key}: {message}")
    raw = str(payload.get("raw", "") or "").strip()
    if raw:
        fragments.append(raw)
    return " | ".join(fragments).strip()


def _extract_project_key(issue_key: str) -> str:
    token = str(issue_key or "").strip().upper()
    match = ISSUE_KEY_PATTERN.match(token)
    if not match:
        return ""
    return match.group(1)


def _extract_cannot_set_fields(payload: Any) -> list[str]:
    errors = payload.get("errors") if isinstance(payload, dict) else None
    if not isinstance(errors, dict):
        return []
    out: list[str] = []
    for key, value in errors.items():
        message = str(value or "").strip().lower()
        if (
            "cannot be set" in message
            or "unknown" in message
            or "does not support update" in message
            or "not supported" in message
            or "must be a string" in message
        ):
            out.append(str(key))
    return out


def _extract_required_field_keys(payload: Any) -> list[str]:
    errors = payload.get("errors") if isinstance(payload, dict) else None
    if not isinstance(errors, dict):
        return []
    out: list[str] = []
    for key, value in errors.items():
        message = str(value or "").strip().lower()
        if "is required" in message:
            out.append(str(key))
    return out


def _is_issue_does_not_exist_error(error: JiraClientError) -> bool:
    if int(error.status or 0) != 404:
        return False
    details = f"{error} {_payload_to_text(getattr(error, 'payload', None))}".lower()
    return "issue does not exist" in details or "issue does not exists" in details or "does not exist" in details


def _pick_required_fields_from_parent(parent_fields: dict[str, Any], required_field_keys: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in required_field_keys:
        if key in parent_fields and parent_fields.get(key) is not None:
            out[key] = parent_fields.get(key)
    return out


def _filter_fields_by_createmeta(fields: dict[str, Any], create_meta_fields: dict[str, Any] | None) -> dict[str, Any]:
    if not create_meta_fields:
        return fields
    always = {"parent", "project", "summary", "issuetype", "description"}
    out: dict[str, Any] = {}
    for key, value in fields.items():
        if key in always or key in create_meta_fields:
            out[key] = value
    return out


def _build_subtask_fields(
    *,
    client: JiraClient,
    parent_issue_key: str,
    summary: str,
    description: str,
    parent_issue: dict[str, Any] | None,
    required_field_keys: list[str],
    parent_by_id: bool,
) -> dict[str, Any]:
    parent_fields = (
        parent_issue.get("fields")
        if isinstance(parent_issue, dict) and isinstance(parent_issue.get("fields"), dict)
        else {}
    )
    inherited = _pick_required_fields_from_parent(parent_fields, required_field_keys)
    project_key = ""
    if isinstance(parent_fields.get("project"), dict):
        project_key = str(parent_fields.get("project", {}).get("key", "") or "").strip()
    if not project_key:
        project_key = _extract_project_key(parent_issue_key)
    project = {"key": project_key} if project_key else {}
    create_meta_fields = client.get_create_meta_fields(project_key, "Sub-task") if project_key else None
    parent_payload: dict[str, str]
    if parent_by_id:
        parent_id = str(parent_issue.get("id", "") if isinstance(parent_issue, dict) else "").strip()
        parent_payload = {"id": parent_id} if parent_id else {"key": parent_issue_key}
    else:
        parent_payload = {"key": parent_issue_key}
    raw_fields: dict[str, Any] = {
        **inherited,
        "parent": parent_payload,
        "project": project,
        "summary": summary,
        "issuetype": {"name": "Sub-task"},
        "description": description,
    }
    return _filter_fields_by_createmeta(raw_fields, create_meta_fields)


def _create_subtask_with_assistant_strategy(
    *,
    client: JiraClient,
    parent_issue_key: str,
    summary: str,
    description: str,
) -> dict[str, Any]:
    parent_issue: dict[str, Any] | None = None
    attempt_fields = _build_subtask_fields(
        client=client,
        parent_issue_key=parent_issue_key,
        summary=summary,
        description=description,
        parent_issue=None,
        required_field_keys=[],
        parent_by_id=False,
    )
    parent_by_id = False
    last_error: JiraClientError | None = None

    for _ in range(SUBTASK_MAX_ATTEMPTS):
        try:
            return client.create_issue(attempt_fields)
        except JiraClientError as exc:
            last_error = exc

            if _is_issue_does_not_exist_error(exc) and not parent_by_id:
                parent_issue = parent_issue or client.get_issue_details(parent_issue_key)
                parent_id = str(parent_issue.get("id", "") if isinstance(parent_issue, dict) else "").strip()
                if parent_id:
                    attempt_fields = {**attempt_fields, "parent": {"id": parent_id}}
                    parent_by_id = True
                    continue

            blocked = _extract_cannot_set_fields(getattr(exc, "payload", None))
            if int(exc.status or 0) == 400 and blocked:
                for key in blocked:
                    attempt_fields.pop(key, None)
                continue

            required = _extract_required_field_keys(getattr(exc, "payload", None))
            if int(exc.status or 0) == 400 and required:
                parent_issue = parent_issue or client.get_issue_details(parent_issue_key)
                next_fields = _build_subtask_fields(
                    client=client,
                    parent_issue_key=parent_issue_key,
                    summary=summary,
                    description=description,
                    parent_issue=parent_issue,
                    required_field_keys=required,
                    parent_by_id=parent_by_id,
                )
                for key in list(attempt_fields.keys()):
                    if key not in next_fields:
                        attempt_fields.pop(key, None)
                attempt_fields.update(next_fields)
                continue

            raise

    if last_error is not None:
        raise last_error
    raise JiraClientError("jira sub-task creation failed after retries", status=None)


def _is_subtask_fallback_error(error: JiraClientError) -> bool:
    status = int(error.status or 0)
    if status not in {400, 403, 404, 422}:
        return False
    details = f"{error} {_payload_to_text(getattr(error, 'payload', None))}".lower()
    tokens = [
        "sub-task",
        "subtask",
        "parent",
        "issue type",
        "issuetype",
        "cannot create",
        "project",
        "project is required",
    ]
    return any(token in details for token in tokens)


def _should_fallback_to_comment(requested_mode: str, error: JiraClientError) -> bool:
    if requested_mode != "auto":
        return False
    status = int(error.status or 0)
    if status == 401:
        return False
    if _is_subtask_fallback_error(error):
        return True
    return True


def _extract_next_subtask_number(subtasks: list[dict[str, Any]]) -> int:
    max_seen = 0
    for item in subtasks:
        if not isinstance(item, dict):
            continue
        summary = _jira_safe_text(str(item.get("summary", "") or ""))
        match = SUBTASK_SUMMARY_PATTERN.match(summary)
        if not match:
            continue
        try:
            max_seen = max(max_seen, int(match.group(1)))
        except ValueError:
            continue
    return max_seen + 1


def _resolve_next_subtask_number(client: JiraClient, issue_key: str, run_id: str, attempts: int) -> int:
    try:
        subtasks = _with_retries(
            attempts=max(1, attempts),
            action="list_subtasks",
            issue_key=issue_key,
            run_id=run_id,
            fn=lambda: client.list_subtasks(issue_key),
        )
    except JiraClientError:
        logger.warning("jira_subtask_number_fallback", issue_key=issue_key, run_id=run_id)
        return 1
    if not isinstance(subtasks, list):
        return 1
    return _extract_next_subtask_number(subtasks)


def _build_subtask_summary(number: int, timestamp_short: str) -> str:
    return f"[bug] VRT #{max(1, int(number))} - {timestamp_short}"


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


def _build_comment_body(
    *,
    run_id: str,
    timestamp: str,
    bug_count: int,
    aso_count: int,
    user_note: str,
    badges: list[str],
    bug_entries: list[dict[str, Any]],
    aso_entries: list[dict[str, Any]],
    aso_mentions: list[str],
    frontend_git: dict[str, str],
    backend_git: dict[str, str],
) -> str:
    front_branch = _escape_table_cell(frontend_git.get("branch", "") or "-")
    front_commit = _escape_table_cell(frontend_git.get("commit", "") or "-")
    back_branch = _escape_table_cell(backend_git.get("branch", "") or "-")
    back_commit = _escape_table_cell(backend_git.get("commit", "") or "-")
    lines: list[str] = [
        "h2. Visual Regression Report",
        f"*Run:* {_escape_table_cell(run_id)}",
        f"*Timestamp:* {_escape_table_cell(timestamp)}",
        f"*Backend Git:* branch={back_branch} | commit={back_commit}",
        f"*Frontend Git:* branch={front_branch} | commit={front_commit}",
        "",
        "*Status badges:*",
    ]
    for badge in badges:
        lines.append(f"- {_jira_safe_text(badge)}")

    if user_note:
        lines.extend(["", "*User note:*", "{quote}", _jira_safe_text(user_note), "{quote}"])

    if bug_entries:
        lines.extend(
            [
                "",
                "----",
                "{panel:title=BUG SECTION|borderStyle=solid|borderColor=#d04437|titleBGColor=#fbeae5|bgColor=#fff}",
                f"*Detected bugs:* {bug_count}",
                "|| # || Scenario || Suite || Target || Full URL || Viewport || Browser || Note || Report || Diff ||",
            ]
        )
        for item in bug_entries:
            target_url = _jira_safe_text(str(item.get("target_url", "") or ""))
            full_url = _jira_safe_text(str(item.get("target_full_url", "") or ""))
            target_cell = (
                _format_jira_link(target_url, full_url) if target_url and full_url else _escape_table_cell(target_url)
            )
            full_url_cell = _format_jira_link("open", full_url) if full_url else "-"
            diff_url = _jira_safe_text(str(item.get("diff_url", "") or ""))
            missing_note = _jira_safe_text(str(item.get("missing_note", "") or ""))
            attachment_thumb = _jira_safe_text(str(item.get("diff_attachment_thumb", "") or ""))
            attachment_file = _jira_safe_text(str(item.get("diff_attachment_file", "") or ""))
            if attachment_thumb:
                diff_cell = f"{attachment_thumb} [^{_escape_table_cell(attachment_file)}]"
            else:
                diff_cell = _format_jira_link("diff", diff_url) if diff_url else _escape_table_cell(missing_note)
            lines.append(
                "| {idx} | {scenario} | {suite} | {target} | {full} | {viewport} | {browser} | {note} | {report} | {diff} |".format(
                    idx=int(item.get("idx", 0) or 0),
                    scenario=_escape_table_cell(str(item.get("scenario", "") or "")),
                    suite=_escape_table_cell(str(item.get("suite_id", "") or "")),
                    target=target_cell,
                    full=full_url_cell,
                    viewport=_escape_table_cell(str(item.get("viewport", "") or "")),
                    browser=_escape_table_cell(str(item.get("browser", "") or "")),
                    note=_escape_table_cell(str(item.get("bug_note", "") or "")),
                    report=_format_jira_link("report", _jira_safe_text(str(item.get("report_url", "") or ""))),
                    diff=diff_cell,
                )
            )
        lines.append("{panel}")

        lines.extend(
            [
                "",
                "{panel:title=BUG DETAILS|borderStyle=solid|borderColor=#f79232|titleBGColor=#fff0d8|bgColor=#fff}",
            ]
        )
        for item in bug_entries:
            lines.append(
                f"*BUG #{int(item.get('idx', 0) or 0)}: {_escape_table_cell(str(item.get('scenario', '') or ''))}*"
            )
            for metadata_line in item.get("metadata_lines", []):
                lines.append(f"- {_jira_safe_text(str(metadata_line or ''))}")
            missing_note = _jira_safe_text(str(item.get("missing_note", "") or ""))
            if missing_note:
                lines.append(f"- Diff attachment: {_escape_table_cell(missing_note)}")
            lines.append("")
        lines.append("{panel}")

    if aso_entries:
        lines.extend(
            [
                "",
                "----",
                "{panel:title=ASO SECTION|borderStyle=solid|borderColor=#f6c342|titleBGColor=#fff4ce|bgColor=#fffef6}",
                f"*Detected ASO requests:* {aso_count}",
            ]
        )
        mentions = " ".join(f"[~{name}]" for name in aso_mentions if _jira_safe_text(name))
        if mentions:
            lines.append(f"*Mentions:* {mentions}")
        lines.append("|| # || Scenario || Target || Full URL || ASO note ||")
        for item in aso_entries:
            target_url = _jira_safe_text(str(item.get("target_url", "") or ""))
            full_url = _jira_safe_text(str(item.get("target_full_url", "") or ""))
            target_cell = (
                _format_jira_link(target_url, full_url) if target_url and full_url else _escape_table_cell(target_url)
            )
            full_url_cell = _format_jira_link("open", full_url) if full_url else "-"
            lines.append(
                "| {idx} | {scenario} | {target} | {full} | {note} |".format(
                    idx=int(item.get("idx", 0) or 0),
                    scenario=_escape_table_cell(str(item.get("scenario", "") or "")),
                    target=target_cell,
                    full=full_url_cell,
                    note=_escape_table_cell(str(item.get("aso_note", "") or "")),
                )
            )
        lines.append("{panel}")

    return "\n".join(lines).strip()


def send_jira_comment(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    issue_key: str,
    user_note: str,
    mode: str,
    auth: dict[str, str] | None,
    scheme: str,
    host: str,
) -> dict[str, Any]:
    client = _build_client(context, auth)
    rows = _read_results_rows(report_dir)
    run_git_info = _extract_run_git_info(rows)
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
    now_local = datetime.now(ZoneInfo("Europe/Warsaw"))
    timestamp = now_local.strftime("%Y-%m-%d %H:%M:%S %Z")
    subtask_timestamp = now_local.strftime("%d/%m/%Y %H:%M")
    badge_lines = _build_badge_line(bug_count, aso_count)
    framework_mode = _normalize_framework_mode(getattr(context, "framework_mode", "server"))
    local_artifacts_mode = framework_mode == "local"
    attachments: list[Path] = []
    bug_entries: list[dict[str, Any]] = []
    aso_entries: list[dict[str, Any]] = []
    fields = _load_bug_pdf_config(context.bug_pdf_config_path).get("fields", [])

    requested_mode = str(mode or "comment").strip().lower()
    if requested_mode not in {"auto", "comment", "subtask"}:
        requested_mode = "comment"

    effective_mode = "comment"
    target_issue = issue_key
    result: Any = {}

    with tempfile.TemporaryDirectory() as scratch:
        scratch_path = Path(scratch)
        for index, case_id in enumerate(bugs, start=1):
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
                    field_lines.append(f"{label}: {value}")
            browser_details = _resolve_browser_details(row, source)
            if browser_details:
                field_lines.append(f"browser.details: {browser_details}")
            diff_rel = str(row.get("diff_path", ""))
            missing_note = None
            diff_url = ""
            diff_attachment_thumb = ""
            diff_attachment_file = ""
            if diff_rel:
                diff_file = (report_dir / diff_rel).resolve(strict=False)
                if local_artifacts_mode:
                    scaled = _prepare_attachment(diff_file, context.jira_pixel_diff_max_width_px, scratch_path)
                    if scaled and scaled.is_file():
                        attachment_name = _build_attachment_filename(
                            idx=index,
                            scenario=str(source["scenario"].get("name", "") or row.get("scenario_id", "scenario")),
                            suffix=Path(scaled).suffix or ".png",
                        )
                        upload_path = scratch_path / attachment_name
                        if scaled.resolve(strict=False) != upload_path.resolve(strict=False):
                            shutil.copy2(scaled, upload_path)
                        attachments.append(upload_path)
                        diff_attachment_file = attachment_name
                        diff_attachment_thumb = f"!{attachment_name}|thumbnail!"
                    else:
                        missing_note = f"{row.get('scenario_id', 'unknown')} ({diff_rel})"
                else:
                    diff_url = (
                        f"{report_url}/{diff_rel}" if base_url else f"/reports/{run_id}/{diff_rel}".replace("//", "/")
                    )
            else:
                missing_note = f"{row.get('scenario_id', 'unknown')} (missing path)"
            bug_entries.append(
                {
                    "idx": index,
                    "scenario": source["scenario"].get("name", ""),
                    "suite_id": source["scenario"].get("suite_id", ""),
                    "target_url": source["scenario"].get("target_url", ""),
                    "target_full_url": source["execution"].get("target_full_url", ""),
                    "viewport": source["scenario"].get("viewport", ""),
                    "browser": source["scenario"].get("browser", ""),
                    "bug_note": source["bug"].get("note", ""),
                    "metadata_lines": field_lines,
                    "report_url": report_url,
                    "diff_url": diff_url,
                    "diff_attachment_thumb": diff_attachment_thumb,
                    "diff_attachment_file": diff_attachment_file,
                    "missing_note": missing_note or "",
                }
            )

        for index, case_id in enumerate(asos, start=1):
            row = rows_by_key.get(case_id)
            if not row:
                continue
            source = _build_metadata_source(row, state.get("test_cases", {}).get(case_id, {}))
            aso_entries.append(
                {
                    "idx": index,
                    "scenario": row.get("scenario_id", "unknown"),
                    "target_url": source["scenario"].get("target_url", ""),
                    "target_full_url": source["execution"].get("target_full_url", ""),
                    "aso_note": source["aso"].get("note", ""),
                }
            )

        comment_body = _build_comment_body(
            run_id=run_id,
            timestamp=timestamp,
            bug_count=bug_count,
            aso_count=aso_count,
            user_note=user_note,
            badges=badge_lines,
            bug_entries=bug_entries,
            aso_entries=aso_entries,
            aso_mentions=list(context.jira_aso_mentions),
            frontend_git=run_git_info.get("frontend", {}),
            backend_git=run_git_info.get("backend", {}),
        )

        if requested_mode in {"auto", "subtask"}:
            next_number = _resolve_next_subtask_number(client, issue_key, run_id, int(context.jira_retry_max))
            summary = _build_subtask_summary(next_number, subtask_timestamp)
            try:
                subtask_result = _with_retries(
                    attempts=1,
                    action="create_subtask",
                    issue_key=issue_key,
                    run_id=run_id,
                    fn=lambda: _create_subtask_with_assistant_strategy(
                        client=client,
                        parent_issue_key=issue_key,
                        summary=summary,
                        description=comment_body,
                    ),
                )
                subtask_key = ""
                if isinstance(subtask_result, dict):
                    subtask_key = str(subtask_result.get("key", "") or "").strip()
                if not subtask_key:
                    raise JiraClientError("jira sub-task response missing key", status=None)
                target_issue = subtask_key
                effective_mode = "subtask"
                result = subtask_result
            except JiraClientError as exc:
                if not _should_fallback_to_comment(requested_mode, exc):
                    raise

        if effective_mode == "comment":
            result = _with_retries(
                attempts=max(1, int(context.jira_retry_max)),
                action="add_comment",
                issue_key=target_issue,
                run_id=run_id,
                fn=lambda: client.add_comment(target_issue, comment_body),
            )

        for attachment in attachments:
            _with_retries(
                attempts=max(1, int(context.jira_retry_max)),
                action="add_attachment",
                issue_key=target_issue,
                run_id=run_id,
                fn=lambda path=attachment: client.add_attachment(target_issue, path),
            )
            time.sleep(max(0, float(context.jira_upload_delay_seconds)))

    if requested_mode in {"auto", "subtask"} and effective_mode == "subtask":
        logger.info("jira_subtask_created", parent_issue=issue_key, subtask=target_issue, run_id=run_id)

    if requested_mode in {"auto", "subtask"} and effective_mode == "comment":
        logger.info("jira_subtask_fallback_to_comment", issue_key=issue_key, run_id=run_id)

    return {
        "issue": target_issue,
        "parent_issue": issue_key,
        "run_id": run_id,
        "framework_mode": framework_mode,
        "mode": effective_mode,
        "requested_mode": requested_mode,
        "attachments": len(attachments),
        "result": result,
    }
