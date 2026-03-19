from __future__ import annotations

import heapq
import queue
import random
import threading
import time
from collections.abc import Callable
from typing import Any

from loguru import logger

from framework.reporting.models import AsyncReportingEvent, AsyncReportingStats

SendCallable = Callable[[str, dict[str, Any]], bool]


class AsyncReportingQueue:
    """In-memory async queue with retry heap and bounded backpressure."""

    def __init__(
        self,
        *,
        enabled: bool,
        queue_maxsize: int,
        max_attempts: int,
        max_retry_age_seconds: int,
        flush_timeout_seconds: int,
        debug_enabled: bool,
        send_callable: SendCallable,
    ) -> None:
        self.enabled = bool(enabled)
        self.queue_maxsize = max(1, int(queue_maxsize))
        self.max_attempts = max(1, int(max_attempts))
        self.max_retry_age_seconds = max(1, int(max_retry_age_seconds))
        self.flush_timeout_seconds = max(1, int(flush_timeout_seconds))
        self.debug_enabled = bool(debug_enabled)
        self._send_callable = send_callable

        self._ready_queue: queue.PriorityQueue[tuple[int, int, AsyncReportingEvent]] = queue.PriorityQueue(
            maxsize=self.queue_maxsize
        )
        self._retry_heap: list[tuple[float, int, AsyncReportingEvent]] = []
        self._retry_lock = threading.Lock()
        self._stats = AsyncReportingStats()
        self._sequence = 0
        self._inflight = 0
        self._inflight_lock = threading.Lock()
        self._flush_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None

    @property
    def stats(self) -> AsyncReportingStats:
        return self._stats

    def start(self) -> None:
        if not self.enabled:
            return
        if self._worker is not None and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._worker_loop, name="reporting-async-worker", daemon=True)
        self._worker.start()
        self._debug(
            "reporting_async_worker_started",
            queue_maxsize=self.queue_maxsize,
            max_attempts=self.max_attempts,
            max_retry_age_seconds=self.max_retry_age_seconds,
            flush_timeout_seconds=self.flush_timeout_seconds,
        )

    def enqueue(self, kind: str, payload: dict[str, Any], priority: int) -> bool:
        if not self.enabled:
            return self._send_callable(kind, payload)
        event = AsyncReportingEvent(
            kind=str(kind or "").strip(),
            payload=dict(payload),
            priority=int(priority),
            sequence=self._next_sequence(),
            created_at_monotonic=time.monotonic(),
        )
        if not self._offer_event(event):
            self._stats.failed += 1
            return False
        self._stats.queued += 1
        self._debug(
            "reporting_async_enqueue",
            kind=event.kind,
            priority=event.priority,
            attempt=event.attempt,
            ready_queue_size=self._ready_queue.qsize(),
            retry_heap_size=self._retry_heap_size(),
        )
        return True

    def flush(self, timeout_seconds: int | None = None) -> bool:
        if not self.enabled:
            return True
        timeout = max(1, int(timeout_seconds or self.flush_timeout_seconds))
        deadline = time.monotonic() + timeout
        with self._flush_lock:
            self._debug(
                "reporting_async_flush_started",
                timeout_seconds=timeout,
                ready_queue_size=self._ready_queue.qsize(),
                retry_heap_size=self._retry_heap_size(),
            )
            while time.monotonic() < deadline:
                self._promote_due_retries()
                if self._ready_queue.empty() and self._retry_heap_size() == 0 and self._inflight_count() == 0:
                    self._debug("reporting_async_flush_finished", success=True)
                    return True
                time.sleep(0.05)
            self._debug(
                "reporting_async_flush_finished",
                success=False,
                ready_queue_size=self._ready_queue.qsize(),
                retry_heap_size=self._retry_heap_size(),
                inflight=self._inflight_count(),
            )
            return False

    def shutdown(self, timeout_seconds: int | None = None) -> None:
        if not self.enabled:
            return
        timeout = max(1, int(timeout_seconds or self.flush_timeout_seconds))
        self._debug("reporting_async_shutdown_requested", timeout_seconds=timeout)
        self.flush(timeout)
        self._stop_event.set()
        if self._worker is not None:
            self._worker.join(timeout=timeout)
        logger.info("reporting_async_shutdown_completed", _skip_remote_log=True, **self._stats.to_dict())

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def _retry_heap_size(self) -> int:
        with self._retry_lock:
            return len(self._retry_heap)

    def _inflight_count(self) -> int:
        with self._inflight_lock:
            return int(self._inflight)

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set() or not self._ready_queue.empty() or self._retry_heap_size() > 0:
            self._promote_due_retries()
            try:
                _, _, event = self._ready_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            self._mark_inflight(1)
            try:
                accepted = bool(self._send_callable(event.kind, event.payload))
            except Exception as exc:
                accepted = False
                self._debug(
                    "reporting_async_send_exception",
                    kind=event.kind,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
            finally:
                self._mark_inflight(-1)
                self._ready_queue.task_done()

            if accepted:
                self._stats.sent += 1
                continue

            self._stats.failed += 1
            now = time.monotonic()
            age_seconds = max(0.0, now - event.created_at_monotonic)
            if event.attempt >= self.max_attempts or age_seconds >= float(self.max_retry_age_seconds):
                self._stats.expired += 1
                self._debug(
                    "reporting_async_event_expired",
                    kind=event.kind,
                    attempt=event.attempt,
                    age_seconds=round(age_seconds, 3),
                )
                continue

            delay = self._retry_delay(event.attempt)
            event.attempt += 1
            event.next_attempt_at_monotonic = now + delay
            self._stats.retried += 1
            self._debug(
                "reporting_async_retry_scheduled",
                kind=event.kind,
                attempt=event.attempt,
                delay_seconds=round(delay, 3),
                next_attempt_at_monotonic=round(event.next_attempt_at_monotonic, 3),
            )
            self._schedule_retry(event)

    def _mark_inflight(self, delta: int) -> None:
        with self._inflight_lock:
            self._inflight += int(delta)

    def _retry_delay(self, current_attempt: int) -> float:
        base = 0.5 * (2 ** max(0, int(current_attempt) - 1))
        jitter = random.uniform(0.0, 0.2)
        return min(10.0, base + jitter)

    def _schedule_retry(self, event: AsyncReportingEvent) -> None:
        with self._retry_lock:
            heapq.heappush(self._retry_heap, (event.next_attempt_at_monotonic, event.sequence, event))

    def _promote_due_retries(self) -> None:
        now = time.monotonic()
        due: list[AsyncReportingEvent] = []
        with self._retry_lock:
            while self._retry_heap and self._retry_heap[0][0] <= now:
                _, _, event = heapq.heappop(self._retry_heap)
                due.append(event)

        for event in due:
            if self._offer_event(event):
                self._debug(
                    "reporting_async_retry_requeued",
                    kind=event.kind,
                    attempt=event.attempt,
                    ready_queue_size=self._ready_queue.qsize(),
                    retry_heap_size=self._retry_heap_size(),
                )
            else:
                self._stats.expired += 1

    def _offer_event(self, event: AsyncReportingEvent) -> bool:
        if self._ready_queue.full():
            if event.kind == "run_finish":
                self._evict_one_non_critical()
            if self._ready_queue.full():
                self._stats.dropped += 1
                logger.warning(
                    "reporting_async_queue_full_drop",
                    _skip_remote_log=True,
                    dropped_kind=event.kind,
                    priority=event.priority,
                    ready_queue_size=self._ready_queue.qsize(),
                )
                return False
        try:
            self._ready_queue.put_nowait((int(event.priority), int(event.sequence), event))
            return True
        except queue.Full:
            self._stats.dropped += 1
            return False

    def _evict_one_non_critical(self) -> None:
        buffered: list[tuple[int, int, AsyncReportingEvent]] = []
        dropped = False
        while not self._ready_queue.empty():
            try:
                current = self._ready_queue.get_nowait()
            except queue.Empty:
                break
            _, _, current_event = current
            if not dropped and current_event.kind in {"log_event", "test_result"}:
                dropped = True
                self._stats.dropped += 1
                self._ready_queue.task_done()
                continue
            buffered.append(current)
            self._ready_queue.task_done()

        for event in buffered:
            try:
                self._ready_queue.put_nowait(event)
            except queue.Full:
                self._stats.dropped += 1
                break

    def _debug(self, message: str, **kwargs: Any) -> None:
        if not self.debug_enabled:
            return
        logger.debug(message, _skip_remote_log=True, **kwargs)
