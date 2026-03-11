from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, BinaryIO

import requests
from loguru import logger


class ReportingHttpSender:
    """Synchronous HTTP sender used by the reporting client and async worker."""

    def __init__(
        self,
        *,
        enabled: bool,
        base_url: str,
        token: str,
        timeout_seconds: int,
        retries: int,
        session: requests.Session,
        thread_local: threading.local,
        debug_async: bool,
    ) -> None:
        self.enabled = bool(enabled)
        self.base_url = str(base_url or "")
        self.token = str(token or "")
        self.timeout_seconds = max(1, int(timeout_seconds))
        self.retries = max(0, int(retries))
        self.session = session
        self._thread_local = thread_local
        self.debug_async = bool(debug_async)

    def _session_for_thread(self) -> requests.Session:
        existing = getattr(self._thread_local, "session", None)
        if isinstance(existing, requests.Session):
            return existing
        if threading.current_thread() is threading.main_thread():
            self._thread_local.session = self.session
            return self.session
        worker_session = requests.Session()
        self._thread_local.session = worker_session
        return worker_session

    def _build_headers(self, payload: dict[str, Any], json_content_type: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {}
        if json_content_type:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        idempotency_key = payload.get("idempotency_key")
        if isinstance(idempotency_key, str) and idempotency_key.strip():
            headers["X-Idempotency-Key"] = idempotency_key.strip()
        return headers

    @staticmethod
    def _extract_screenshot_paths(payload: dict[str, Any]) -> list[Path]:
        artifacts = payload.get("artifacts")
        raw_paths: list[str] = []

        if isinstance(artifacts, dict):
            for key in ("screenshot_raw", "screenshot_annotated"):
                path_value = artifacts.get(key)
                if isinstance(path_value, str) and path_value.strip():
                    raw_paths.append(path_value.strip())
        elif isinstance(artifacts, list):
            for row in artifacts:
                if not isinstance(row, dict):
                    continue
                kind = str(row.get("kind") or "").strip()
                if kind not in {"screenshot_raw", "screenshot_annotated"}:
                    continue
                path_value = row.get("path")
                if isinstance(path_value, str) and path_value.strip():
                    raw_paths.append(path_value.strip())

        deduplicated_paths = dict.fromkeys(raw_paths)
        return [Path(path) for path in deduplicated_paths]

    @staticmethod
    def _is_failure_with_screenshots(payload: dict[str, Any]) -> bool:
        if payload.get("status") != "failed":
            return False
        return bool(ReportingHttpSender._extract_screenshot_paths(payload))

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code <= 599

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        time.sleep(0.5 * (attempt + 1))

    @staticmethod
    def _payload_hash(payload: dict[str, Any]) -> str:
        try:
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        except TypeError:
            raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _thread_context() -> dict[str, str]:
        thread = threading.current_thread()
        return {
            "thread_name": str(thread.name or ""),
            "thread_id": str(threading.get_ident()),
        }

    @staticmethod
    def _log_context_from_payload(payload: dict[str, Any]) -> dict[str, str]:
        run_id = str(payload.get("run_id", "") or "")
        run_uid = str(payload.get("run_uid", "") or "")
        test_id = str(payload.get("test_id", "") or "")
        event_type = str(payload.get("event_type", "") or "")

        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        tester = str(metadata.get("tester", "") or "")
        run_note = str(metadata.get("run_note", "") or "")

        return {
            "run_id": run_id,
            "run_uid": run_uid,
            "test_id": test_id,
            "event_type": event_type,
            "tester": tester,
            "run_note": run_note,
        }

    def _debug_async_log(self, message: str, **kwargs: Any) -> None:
        if not self.debug_async:
            return
        logger.debug(message, _skip_remote_log=True, **kwargs)

    def post_json(self, path: str, payload: dict[str, Any], *, queue_event_type: str = "") -> bool:
        if not self.enabled or not self.base_url:
            return False

        url = f"{self.base_url.rstrip('/')}{path}"
        headers = self._build_headers(payload, json_content_type=True)
        context = {**self._log_context_from_payload(payload), **self._thread_context()}
        payload_hash = self._payload_hash(payload)
        self._debug_async_log(
            "reporting_async_http_send_start",
            endpoint=path,
            queue_event_type=queue_event_type,
            payload_hash=payload_hash,
        )

        for attempt in range(self.retries + 1):
            try:
                logger.debug(
                    "reporting_api_post_attempt",
                    endpoint=path,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    max_retries=self.retries,
                    timeout_seconds=self.timeout_seconds,
                    payload_hash=payload_hash,
                    payload_size=len(json.dumps(payload, default=str)),
                    _skip_remote_log=True,
                    **context,
                )
                response = self._session_for_thread().post(
                    url, json=payload, headers=headers, timeout=self.timeout_seconds
                )
            except requests.RequestException as exc:
                logger.warning(
                    "reporting_api_request_exception",
                    endpoint=path,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    error=str(exc),
                    error_type=type(exc).__name__,
                    payload_hash=payload_hash,
                    _skip_remote_log=True,
                    **context,
                )
                if attempt < self.retries:
                    self._sleep_backoff(attempt)
                continue

            if response.ok:
                logger.info(
                    "reporting_api_call_success",
                    endpoint=path,
                    url=url,
                    method="POST",
                    status=response.status_code,
                    payload_hash=payload_hash,
                    _skip_remote_log=True,
                    **context,
                )
                return True

            try:
                preview = response.text[:200]
            except Exception:
                preview = ""
            logger.warning(
                "reporting_api_non_2xx",
                endpoint=path,
                status=response.status_code,
                url=url,
                method="POST",
                payload_hash=payload_hash,
                response_preview=preview,
                _skip_remote_log=True,
                **context,
            )
            if attempt < self.retries and self._should_retry_status(response.status_code):
                self._sleep_backoff(attempt)
                continue
            logger.error(
                "reporting_api_call_failed",
                endpoint=path,
                url=url,
                method="POST",
                status=response.status_code,
                payload_hash=payload_hash,
                response_preview=preview,
                _skip_remote_log=True,
                **context,
            )
            return False

        logger.critical(
            "reporting_api_call_final_failure",
            endpoint=path,
            url=url,
            method="POST",
            total_attempts=self.retries + 1,
            payload_hash=payload_hash,
            _skip_remote_log=True,
            **context,
        )
        return False

    def post_test_result(self, endpoint: str, payload: dict[str, Any], *, queue_event_type: str = "") -> bool:
        if not self.enabled or not self.base_url:
            return False
        if not self._is_failure_with_screenshots(payload):
            return self.post_json(endpoint, payload, queue_event_type=queue_event_type)

        url = f"{self.base_url.rstrip('/')}{endpoint}"
        existing_paths = [path for path in self._extract_screenshot_paths(payload) if path.is_file()]
        if not existing_paths:
            return self.post_json(endpoint, payload, queue_event_type=queue_event_type)

        headers = self._build_headers(payload, json_content_type=False)
        context = {**self._log_context_from_payload(payload), **self._thread_context()}
        payload_hash = self._payload_hash(payload)
        self._debug_async_log(
            "reporting_async_http_send_start",
            endpoint=endpoint,
            queue_event_type=queue_event_type,
            payload_hash=payload_hash,
            files_count=len(existing_paths),
        )

        for attempt in range(self.retries + 1):
            opened_handles: list[BinaryIO] = []
            try:
                logger.debug(
                    "reporting_api_post_files_attempt",
                    endpoint=endpoint,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    max_retries=self.retries,
                    timeout_seconds=self.timeout_seconds,
                    payload_hash=payload_hash,
                    file_count=len(existing_paths),
                    _skip_remote_log=True,
                    **context,
                )
                files = []
                for file_path in existing_paths:
                    handle = file_path.open("rb")
                    opened_handles.append(handle)
                    files.append(("screenshots", (file_path.name, handle, "image/png")))

                response = self._session_for_thread().post(
                    url,
                    data={"payload": json.dumps(payload)},
                    files=files,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                if response.ok:
                    logger.info(
                        "reporting_api_call_success",
                        endpoint=endpoint,
                        url=url,
                        method="POST",
                        status=response.status_code,
                        payload_hash=payload_hash,
                        _skip_remote_log=True,
                        **context,
                    )
                    return True

                try:
                    preview = response.text[:200]
                except Exception:
                    preview = ""
                logger.warning(
                    "reporting_api_non_2xx",
                    endpoint=endpoint,
                    status=response.status_code,
                    url=url,
                    method="POST",
                    payload_hash=payload_hash,
                    response_preview=preview,
                    _skip_remote_log=True,
                    **context,
                )
                if attempt < self.retries and self._should_retry_status(response.status_code):
                    self._sleep_backoff(attempt)
                    continue
                logger.error(
                    "reporting_api_call_failed",
                    endpoint=endpoint,
                    url=url,
                    method="POST",
                    status=response.status_code,
                    payload_hash=payload_hash,
                    response_preview=preview,
                    _skip_remote_log=True,
                    **context,
                )
                return False
            except requests.RequestException as exc:
                logger.warning(
                    "reporting_api_files_upload_exception",
                    endpoint=endpoint,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    error=str(exc),
                    error_type=type(exc).__name__,
                    payload_hash=payload_hash,
                    _skip_remote_log=True,
                    **context,
                )
                if attempt < self.retries:
                    self._sleep_backoff(attempt)
                continue
            finally:
                for handle in opened_handles:
                    try:
                        handle.close()
                    except Exception:
                        pass

        logger.critical(
            "reporting_api_call_final_failure",
            endpoint=endpoint,
            url=url,
            method="POST",
            total_attempts=self.retries + 1,
            payload_hash=payload_hash,
            _skip_remote_log=True,
            **context,
        )
        return self.post_json(endpoint, payload, queue_event_type=queue_event_type)
