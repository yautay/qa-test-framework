from __future__ import annotations

from typing import Final

LOG_LEVEL_TO_NO: Final[dict[str, int]] = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def normalize_log_level(value: str, default: str = "WARNING") -> str:
    token = str(value or "").strip().upper()
    if token == "WARN":
        token = "WARNING"
    fallback = str(default or "WARNING").strip().upper()
    if fallback == "WARN":
        fallback = "WARNING"
    if fallback not in LOG_LEVEL_TO_NO:
        fallback = "WARNING"
    return token if token in LOG_LEVEL_TO_NO else fallback


def level_to_no(value: str, default: str = "WARNING") -> int:
    return LOG_LEVEL_TO_NO[normalize_log_level(value, default=default)]
