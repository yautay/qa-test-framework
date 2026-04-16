from __future__ import annotations

import importlib
import inspect
import threading
import time
from collections.abc import Callable
from contextlib import nullcontext
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypeVar, cast

try:
    allure = importlib.import_module("allure")
except Exception:
    allure = None

T = TypeVar("T", bound=Callable[..., Any])

_CURRENT_TEST_NODEID: ContextVar[str] = ContextVar("_CURRENT_TEST_NODEID", default="")
_STEP_TRACES: dict[str, list[dict[str, object]]] = {}
_LOCK = threading.RLock()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_title(value: str, fallback: str = "step") -> str:
    text = str(value or "").strip()
    return text or fallback


def _resolve_title_template(
    template: str, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> str:
    title = _normalize_title(template, fallback=getattr(func, "__name__", "step"))
    try:
        bound = inspect.signature(func).bind_partial(*args, **kwargs)
        bound.apply_defaults()
        rendered = title.format(**bound.arguments)
        return _normalize_title(rendered, fallback=title)
    except Exception:
        return title


def start_test_step_trace(nodeid: str) -> Token[str]:
    normalized = str(nodeid or "").strip()
    with _LOCK:
        _STEP_TRACES[normalized] = []
    return _CURRENT_TEST_NODEID.set(normalized)


def stop_test_step_trace(token: Token[str]) -> None:
    _CURRENT_TEST_NODEID.reset(token)


def pop_test_step_trace(nodeid: str) -> list[dict[str, object]]:
    normalized = str(nodeid or "").strip()
    with _LOCK:
        rows = _STEP_TRACES.pop(normalized, [])
    return [dict(row) for row in rows if isinstance(row, dict)]


def _record_step(
    *,
    title: str,
    status: str,
    started_at: str,
    finished_at: str,
    duration_ms: int,
    error: str,
) -> None:
    nodeid = str(_CURRENT_TEST_NODEID.get() or "").strip()
    if not nodeid:
        return

    payload: dict[str, object] = {
        "title": _normalize_title(title),
        "status": str(status or "unknown").strip().lower() or "unknown",
        "started_at": str(started_at or ""),
        "finished_at": str(finished_at or ""),
        "duration_ms": max(0, int(duration_ms)),
    }
    error_message = str(error or "").strip()
    if error_message:
        payload["error"] = error_message[:1000]

    with _LOCK:
        bucket = _STEP_TRACES.setdefault(nodeid, [])
        bucket.append(payload)


class _StepContext:
    def __init__(self, title: str) -> None:
        self._title = _normalize_title(title)
        self._started_at = ""
        self._started_perf = 0.0
        self._allure_context: Any = nullcontext()

    def __enter__(self) -> _StepContext:
        self._started_at = _utc_now()
        self._started_perf = time.perf_counter()
        if allure is not None:
            self._allure_context = allure.step(self._title)
        self._allure_context.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool | None:
        finished_at = _utc_now()
        elapsed_ms = int(max(0.0, time.perf_counter() - self._started_perf) * 1000)
        error_message = ""
        status = "passed"
        if exc is not None:
            status = "failed"
            error_message = str(exc)
        _record_step(
            title=self._title,
            status=status,
            started_at=self._started_at,
            finished_at=finished_at,
            duration_ms=elapsed_ms,
            error=error_message,
        )
        return cast(bool | None, self._allure_context.__exit__(exc_type, exc, tb))


def step_context(title: str) -> _StepContext:
    return _StepContext(title)


def step(title: str) -> Callable[[T], T]:
    """Safe allure.step decorator with per-test step tracing."""

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any):
            rendered_title = _resolve_title_template(title, cast(Callable[..., Any], func), args, kwargs)
            with step_context(rendered_title):
                return func(*args, **kwargs)

        return cast(T, wrapped)

    return decorator


def feature(name: str) -> Callable[[T], T]:
    """Safe allure.feature decorator."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return cast(Callable[[T], T], allure.feature(name))


def story(name: str) -> Callable[[T], T]:
    """Safe allure.story decorator."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return cast(Callable[[T], T], allure.story(name))


def severity(level: Any) -> Callable[[T], T]:
    """Safe allure.severity decorator."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return cast(Callable[[T], T], allure.severity(level))
