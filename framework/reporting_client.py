from __future__ import annotations

"""Client that delivers test-run metadata and screenshots to the reporting API."""

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import requests
from loguru import logger


@dataclass
class ReportingClient:
    """Encapsulates reporting endpoints, retries, and authentication headers."""

    enabled: bool
    base_url: str
    token: str
    run_start_endpoint: str = "/test-run/start"
    test_result_endpoint: str = "/test-run/test-result"
    run_finish_endpoint: str = "/test-run/finish"
    timeout_seconds: int = 5
    retries: int = 2

    # Reuse TCP connections
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    _thread_local: threading.local = field(default_factory=threading.local, repr=False)

    def _session(self) -> requests.Session:
        existing = getattr(self._thread_local, "session", None)
        if isinstance(existing, requests.Session):
            return existing
        if threading.current_thread() is threading.main_thread():
            self._thread_local.session = self.session
            return self.session
        worker_session = requests.Session()
        self._thread_local.session = worker_session
        return worker_session

    def _build_headers(self, payload: dict, json_content_type: bool = True) -> dict[str, str]:
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
    def _is_failure_with_screenshots(payload: dict) -> bool:
        if payload.get("status") != "failed":
            return False
        return bool(ReportingClient._extract_screenshot_paths(payload))

    @staticmethod
    def _extract_screenshot_paths(payload: dict) -> list[Path]:
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
    def _should_retry_status(status_code: int) -> bool:
        # Retry on rate limit and server errors; avoid retrying most client errors.
        return status_code == 429 or 500 <= status_code <= 599

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        # Simple linear backoff: 0.5s, 1.0s, 1.5s ...
        time.sleep(0.5 * (attempt + 1))

    @staticmethod
    def _payload_hash(payload: dict) -> str:
        try:
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        except TypeError:
            raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _post(self, path: str, payload: dict) -> bool:
        if not self.enabled or not self.base_url:
            return False

        url = f"{self.base_url.rstrip('/')}{path}"
        headers = self._build_headers(payload, json_content_type=True)
        context = {**self._log_context_from_payload(payload), **self._thread_context()}
        payload_hash = self._payload_hash(payload)

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
                    **context,
                )
                response = self._session().post(url, json=payload, headers=headers, timeout=self.timeout_seconds)
            except requests.RequestException as e:
                logger.warning(
                    "reporting_api_request_exception",
                    endpoint=path,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    error=str(e),
                    error_type=type(e).__name__,
                    payload_hash=payload_hash,
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
                **context,
            )
            return False  # do not retry non-retriable status codes

        logger.critical(
            "reporting_api_call_final_failure",
            endpoint=path,
            url=url,
            method="POST",
            total_attempts=self.retries + 1,
            payload_hash=payload_hash,
            **context,
        )
        return False

    def _post_test_result_with_screenshots(self, payload: dict) -> bool:
        if not self.enabled or not self.base_url:
            return False

        url = f"{self.base_url.rstrip('/')}{self.test_result_endpoint}"
        existing_paths = [path for path in self._extract_screenshot_paths(payload) if path.is_file()]
        if not existing_paths:
            return self._post(self.test_result_endpoint, payload)

        headers = self._build_headers(payload, json_content_type=False)
        context = {**self._log_context_from_payload(payload), **self._thread_context()}
        payload_hash = self._payload_hash(payload)

        for attempt in range(self.retries + 1):
            opened_handles: list[BinaryIO] = []
            try:
                logger.debug(
                    "reporting_api_post_files_attempt",
                    endpoint=self.test_result_endpoint,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    max_retries=self.retries,
                    timeout_seconds=self.timeout_seconds,
                    payload_hash=payload_hash,
                    file_count=len(existing_paths),
                    **context,
                )
                files = []
                for file_path in existing_paths:
                    handle = file_path.open("rb")
                    opened_handles.append(handle)
                    files.append(("screenshots", (file_path.name, handle, "image/png")))

                data = {"payload": json.dumps(payload)}
                response = self._session().post(
                    url,
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                if response.ok:
                    logger.info(
                        "reporting_api_call_success",
                        endpoint=self.test_result_endpoint,
                        url=url,
                        method="POST",
                        status=response.status_code,
                        payload_hash=payload_hash,
                        **context,
                    )
                    return True

                try:
                    preview = response.text[:200]
                except Exception:
                    preview = ""
                logger.warning(
                    "reporting_api_non_2xx",
                    endpoint=self.test_result_endpoint,
                    status=response.status_code,
                    url=url,
                    method="POST",
                    payload_hash=payload_hash,
                    response_preview=preview,
                    **context,
                )

                if attempt < self.retries and self._should_retry_status(response.status_code):
                    self._sleep_backoff(attempt)
                    continue

                logger.error(
                    "reporting_api_call_failed",
                    endpoint=self.test_result_endpoint,
                    url=url,
                    method="POST",
                    status=response.status_code,
                    payload_hash=payload_hash,
                    response_preview=preview,
                    **context,
                )
                return False  # do not retry non-retriable status codes

            except requests.RequestException as e:
                logger.warning(
                    "reporting_api_files_upload_exception",
                    endpoint=self.test_result_endpoint,
                    url=url,
                    method="POST",
                    attempt=attempt,
                    error=str(e),
                    error_type=type(e).__name__,
                    payload_hash=payload_hash,
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
            endpoint=self.test_result_endpoint,
            url=url,
            method="POST",
            total_attempts=self.retries + 1,
            payload_hash=payload_hash,
            **context,
        )
        # Final fallback: JSON-only
        return self._post(self.test_result_endpoint, payload)

    def run_start(self, payload: dict) -> None:
        self._post(self.run_start_endpoint, payload)

    def test_result(self, payload: dict) -> None:
        if self._is_failure_with_screenshots(payload):
            self._post_test_result_with_screenshots(payload)
            return
        self._post(self.test_result_endpoint, payload)

    def run_finish(self, payload: dict) -> None:
        self._post(self.run_finish_endpoint, payload)

    def send_payload(self, endpoint: str, payload: dict) -> bool:
        return self._post(endpoint, payload)

    @staticmethod
    def _log_context_from_payload(payload: dict) -> dict[str, str]:
        run_id = str(payload.get("run_id", "") or "")
        test_id = str(payload.get("test_id", "") or "")
        event_type = str(payload.get("event_type", "") or "")

        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        tester = str(metadata.get("tester", "") or "")
        run_note = str(metadata.get("run_note", "") or "")

        if not tester or not run_note:
            run_context = payload.get("run_context")
            if isinstance(run_context, dict):
                run_start = run_context.get("run_start")
                if isinstance(run_start, dict):
                    run_meta = run_start.get("metadata")
                    if isinstance(run_meta, dict):
                        tester = tester or str(run_meta.get("tester", "") or "")
                        run_note = run_note or str(run_meta.get("run_note", "") or "")

        return {
            "run_id": run_id,
            "test_id": test_id,
            "event_type": event_type,
            "tester": tester,
            "run_note": run_note,
        }

    @staticmethod
    def _thread_context() -> dict[str, str]:
        thread = threading.current_thread()
        return {
            "thread_name": str(thread.name or ""),
            "thread_id": str(threading.get_ident()),
        }
