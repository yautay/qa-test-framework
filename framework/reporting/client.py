from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import threading
from typing import Any

import requests

from framework.log_levels import level_to_no, normalize_log_level
from framework.reporting.async_queue import AsyncReportingQueue
from framework.reporting.http_sender import ReportingHttpSender


@dataclass
class ReportingClient:
    """Encapsulates reporting endpoints and optional async dispatch queue."""

    enabled: bool
    base_url: str
    token: str
    run_start_endpoint: str = "/test-run/start"
    test_result_endpoint: str = "/test-run/test-result"
    run_finish_endpoint: str = "/test-run/finish"
    log_endpoint: str = "/test-run/log"
    log_level: str = "WARNING"
    timeout_seconds: int = 5
    retries: int = 2
    async_enabled: bool = False
    async_queue_maxsize: int = 1000
    async_max_attempts: int = 3
    async_max_retry_age_seconds: int = 30
    async_flush_timeout_seconds: int = 3

    session: requests.Session = field(default_factory=requests.Session, repr=False)
    _thread_local: threading.local = field(default_factory=threading.local, repr=False)

    def __post_init__(self) -> None:
        normalized_level = self._normalize_level_name(self.log_level)
        self.log_level = normalized_level
        self._debug_async = normalized_level == "DEBUG"
        self._sender = ReportingHttpSender(
            enabled=self.enabled,
            base_url=self.base_url,
            token=self.token,
            timeout_seconds=self.timeout_seconds,
            retries=self.retries,
            session=self.session,
            thread_local=self._thread_local,
            debug_async=self._debug_async,
        )
        self._queue = AsyncReportingQueue(
            enabled=self.enabled and self.async_enabled,
            queue_maxsize=self.async_queue_maxsize,
            max_attempts=self.async_max_attempts,
            max_retry_age_seconds=self.async_max_retry_age_seconds,
            flush_timeout_seconds=self.async_flush_timeout_seconds,
            debug_enabled=self._debug_async,
            send_callable=self._send_event_sync,
        )
        self._queue.start()

    @classmethod
    def _normalize_level_name(cls, value: str, default: str = "WARNING") -> str:
        return normalize_log_level(value, default=default)

    @classmethod
    def _level_no(cls, value: str) -> int:
        return level_to_no(value, default="WARNING")

    def _should_send_log_level(self, level: str) -> bool:
        threshold = self._level_no(self.log_level)
        return self._level_no(level) >= threshold

    def _send_event_sync(self, event_type: str, payload: dict[str, Any]) -> bool:
        self._sender.session = self.session
        token = str(event_type or "").strip().lower()
        if token == "run_start":
            return self._sender.post_json(self.run_start_endpoint, payload, queue_event_type=token)
        if token == "test_result":
            return self._sender.post_test_result(self.test_result_endpoint, payload, queue_event_type=token)
        if token == "run_finish":
            return self._sender.post_json(self.run_finish_endpoint, payload, queue_event_type=token)
        if token == "log_event":
            return self._sender.post_json(self.log_endpoint, payload, queue_event_type=token)
        endpoint = str(payload.get("_endpoint", "") or "")
        if endpoint:
            clean_payload = dict(payload)
            clean_payload.pop("_endpoint", None)
            return self._sender.post_json(endpoint, clean_payload, queue_event_type=token or "custom")
        return False

    def _event_priority(self, event_type: str) -> int:
        token = str(event_type or "").strip().lower()
        if token == "run_finish":
            return 0
        if token == "run_start":
            return 1
        if token == "test_result":
            return 2
        if token == "log_event":
            return 3
        return 2

    def _dispatch(self, event_type: str, payload: dict[str, Any]) -> bool:
        if self.enabled and self.async_enabled:
            return self._queue.enqueue(event_type, payload, self._event_priority(event_type))
        return self._send_event_sync(event_type, payload)

    def run_start(self, payload: dict[str, Any]) -> None:
        self._dispatch("run_start", payload)

    def test_result(self, payload: dict[str, Any]) -> None:
        self._dispatch("test_result", payload)

    def run_finish(self, payload: dict[str, Any]) -> None:
        self._dispatch("run_finish", payload)

    def log_event(
        self,
        *,
        level: str,
        message: str,
        run_id: str,
        nodeid: str,
        metadata: dict[str, str] | None = None,
        timestamp: str = "",
        extra: dict[str, Any] | None = None,
    ) -> bool:
        if not self.enabled or not self.base_url:
            return False

        normalized_level = self._normalize_level_name(level)
        if not self._should_send_log_level(normalized_level):
            return False

        payload: dict[str, Any] = {
            "event_type": "log",
            "timestamp": timestamp or datetime.now(UTC).isoformat(),
            "level": normalized_level,
            "message": str(message or ""),
            "run_id": str(run_id or ""),
            "nodeid": str(nodeid or ""),
            "metadata": metadata or {},
        }
        if isinstance(extra, dict) and extra:
            payload["extra"] = extra
        return self._dispatch("log_event", payload)

    def send_payload(self, endpoint: str, payload: dict[str, Any]) -> bool:
        # Keep this path synchronous for report-server service flows.
        wrapped = dict(payload)
        wrapped["_endpoint"] = endpoint
        return self._send_event_sync("custom", wrapped)

    def flush(self, timeout_seconds: int | None = None) -> bool:
        return self._queue.flush(timeout_seconds=timeout_seconds)

    def shutdown(self, timeout_seconds: int | None = None) -> None:
        self._queue.shutdown(timeout_seconds=timeout_seconds)
