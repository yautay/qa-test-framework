from __future__ import annotations

import json
import re
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

from loguru import logger

from ..constants import CHALLENGE_TTL_SECONDS
from ..context import ChallengeEntry, ReportServerContext
from ..paths import _build_dir, _resolve_actual_png, _safe_run_id_or_error
from ..reports import _list_reports_payload, _read_build_metadata, _read_results_rows, _read_run_metadata
from ..services.pdf import _generate_bug_pdf
from ..services.sync import (
    _apply_event_to_state,
    _flush_pending,
    _mark_case_synced,
    _row_tag_key,
    _schedule_outbox_event,
)
from ..state import (
    TEXT_MAX_LENGTH,
    _acquire_lock,
    _ensure_case_state,
    _heartbeat_lock,
    _load_state,
    _normalize_text,
    _record_event_attempt,
    _release_lock,
    _save_state,
    _treat_reporting_disabled_as_success,
)
from ..utils.app_info import _build_app_info_payload
from ..utils.challenges import _cleanup_expired_challenges, _generate_phrase
from ..utils.http import _json_bytes, _serve_file
from ..utils.perceptual import _perceptual_health_payload, _perceptual_queue_payload
from ..utils.validation import _as_non_empty_text, _validated_text


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
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as exc:
                logger.debug(
                    "reporting_client_disconnected_before_response",
                    status=status,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
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

            m_tags = re.match(r"^/api/builds/([^/]+)/tags$", path)
            if m_tags:
                try:
                    run_id = _safe_run_id_or_error(m_tags.group(1))
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
                self._send_json(HTTPStatus.OK, {"run_id": run_id, "tags": state})
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
                build_metadata = _read_build_metadata(run_dir)
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
                self._send_json(
                    HTTPStatus.OK,
                    {"run_id": run_id, "results": enriched_rows, "build_metadata": build_metadata},
                )
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
                logger.opt(exception=True).warning("report_server_get_failed", path=self.path)
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
                    from secrets import token_urlsafe

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
                logger.opt(exception=True).warning("report_server_post_failed", path=self.path)
                try:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal server error"})
                except Exception:
                    return

    return Handler
