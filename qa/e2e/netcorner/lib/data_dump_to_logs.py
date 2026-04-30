from __future__ import annotations

import json
import threading
from contextvars import ContextVar, Token
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

_CURRENT_TEST_NODEID: ContextVar[str] = ContextVar("_CURRENT_TEST_DATA_DUMP_NODEID", default="")
_TEST_DATA_DUMPS: dict[str, dict[str, Any]] = {}
_LOCK = threading.RLock()


def _serialize_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _serialize_value(asdict(value))
    if isinstance(value, Enum):
        return _serialize_value(value.value)
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def start_test_data_dump(nodeid: str) -> Token[str]:
    normalized = str(nodeid or "").strip()
    with _LOCK:
        _TEST_DATA_DUMPS[normalized] = {}
    return _CURRENT_TEST_NODEID.set(normalized)


def stop_test_data_dump(token: Token[str]) -> None:
    _CURRENT_TEST_NODEID.reset(token)


def dump_data(**kwargs: Any) -> None:
    nodeid = str(_CURRENT_TEST_NODEID.get() or "").strip()
    if not nodeid:
        raise RuntimeError("dump_data() called outside of an active test context")

    serialized = {str(key): _serialize_value(value) for key, value in kwargs.items()}
    with _LOCK:
        bucket = _TEST_DATA_DUMPS.setdefault(nodeid, {})
        bucket.update(serialized)


def pop_test_data_dump(nodeid: str) -> dict[str, Any]:
    normalized = str(nodeid or "").strip()
    with _LOCK:
        payload = _TEST_DATA_DUMPS.pop(normalized, {})
    return dict(payload) if isinstance(payload, dict) else {}


def format_dump_for_log(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
