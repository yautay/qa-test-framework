from __future__ import annotations

import logging
import os
import re
import socket
import sys
from pathlib import Path
from typing import Any, cast

from loguru import logger

import settings
from framework.log_levels import normalize_log_level

_REDACTED = "***REDACTED***"
_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "accesskey",
    "authorization",
    "cookie",
    "session",
    "private_key",
)

_INLINE_SECRET_PATTERN = re.compile(
    r"(?i)\b(authorization|token|password|passwd|secret|api[_-]?key|access[_-]?key)\b\s*[:=]\s*([^\s,;]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\b(Bearer)\s+([A-Za-z0-9._~+/=-]+)")
_URL_CREDENTIALS_PATTERN = re.compile(r"(?i)(https?://)([^\s/@:]+):([^\s/@]+)@")

"""Loguru helpers that bind execution context and channel logs to stdout + JSON file.

Best practices implemented:
- stdout: human-readable logs (no JSON) for developer ergonomics
- file: JSON logs (serialize=True) for ingestion and post-run analysis
- per-worker file logs to avoid contention/rotation races in parallel execution
- rotation/retention/compression configurable via env vars
- safe default `nodeid="(session)"` to prevent format KeyError before binding test context
"""


def _resolve_console_log_level() -> str:
    """Normalize console log level from env/settings, falling back to WARNING."""
    value = os.getenv("CONSOLE_LOG_LEVEL", getattr(settings, "console_log_level", "WARNING"))
    return normalize_log_level(str(value), default="WARNING")


def _normalize_log_level(value: str, default: str = "WARNING") -> str:
    return normalize_log_level(value, default=default)


def _is_sensitive_key(key: str) -> bool:
    token = str(key or "").strip().lower()
    return any(fragment in token for fragment in _SENSITIVE_KEY_FRAGMENTS)


def _redact_text(value: str) -> str:
    text = str(value or "")
    text = _BEARER_PATTERN.sub(lambda m: f"{m.group(1)} {_REDACTED}", text)
    text = _URL_CREDENTIALS_PATTERN.sub(lambda m: f"{m.group(1)}{_REDACTED}:{_REDACTED}@", text)
    text = _INLINE_SECRET_PATTERN.sub(lambda m: f"{m.group(1)}={_REDACTED}", text)
    return text


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: (_REDACTED if _is_sensitive_key(str(key)) else _redact_value(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _redact_record(record: Any) -> None:
    if not isinstance(record, dict):
        return
    record["message"] = _redact_text(str(record.get("message", "")))
    extra = record.get("extra")
    if isinstance(extra, dict):
        record["extra"] = _redact_value(extra)


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _install_stdlib_logging_bridge() -> None:
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    logging.captureWarnings(True)


def _sanitize_worker_id(worker_id: str) -> str:
    """Make worker id safe for filenames."""
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in worker_id.strip())
    return safe or "w0"


def _resolve_log_option(env_name: str, settings_name: str, default: str) -> str:
    value = os.getenv(env_name, getattr(settings, settings_name, default))
    normalized = str(value).strip()
    return normalized or default


def _console_stream() -> Any:
    stream = getattr(sys, "__stdout__", None)
    return stream if stream is not None else sys.stdout


def configure_logging(
    run_log_dir: Path,
    run_id: str,
    browser: str,
    worker_id: str,
    git_user_name: str | None,
    git_user_email: str | None,
    tester: str = "",
    run_note: str = "",
) -> Path:
    """Prepare console + file sinks and attach tracer metadata for Loguru.

    Returns
    -------
    Path
        The per-worker log file path.
    """
    logger.remove()
    _install_stdlib_logging_bridge()
    run_log_dir.mkdir(parents=True, exist_ok=True)

    hostname = socket.gethostname()
    base_extra = {
        "run_id": run_id,
        "hostname": hostname,
        "browser": browser,
        "worker_id": worker_id,
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
        "tester": str(tester or ""),
        "run_note": str(run_note or ""),
        "nodeid": "(session)",  # safe default until bind_test_context() is used
    }
    logger.configure(extra=base_extra, patcher=cast(Any, _redact_record))

    # Human-readable console sink
    logger.add(
        _console_stream(),
        level=_resolve_console_log_level(),
        enqueue=False,  # console is fine without queue; lower overhead
        serialize=False,
        backtrace=False,
        diagnose=False,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "{extra[run_id]} | {extra[worker_id]} | {extra[browser]} | "
            "tester={extra[tester]} | "
            "note={extra[run_note]} | "
            "{extra[hostname]} | "
            "{extra[nodeid]} | "
            "{message}"
        ),
    )

    # Per-worker JSON file sink
    worker_safe = _sanitize_worker_id(worker_id)
    log_file = (run_log_dir / f"run_{run_id}_{worker_safe}.log").resolve()

    logger.add(
        str(log_file),
        level="DEBUG",
        enqueue=True,  # safer for file writes
        serialize=True,  # machine-readable JSON
        backtrace=True,  # richer error context in file logs
        diagnose=True,
        rotation=_resolve_log_option("LOG_ROTATION", "log_rotation", "50 MB"),
        retention=_resolve_log_option("LOG_RETENTION", "log_retention", "7 days"),
        compression=_resolve_log_option("LOG_COMPRESSION", "log_compression", "zip"),
    )

    return log_file


def add_tools_file_sink(script_name: str) -> Path:
    """Add per-script file sink under tools/logs without touching existing sinks."""
    root = Path(__file__).resolve().parents[1]
    logs_rel = str(getattr(settings, "tools_logs_dir", "tools/logs") or "tools/logs")
    logs_dir = (root / logs_rel).resolve()
    logs_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_worker_id(script_name)
    log_path = (logs_dir / f"{safe_name}.log").resolve()
    logger.add(
        str(log_path),
        level=_resolve_log_option("TOOLS_FILE_LOG_LEVEL", "tools_file_log_level", "DEBUG"),
        enqueue=True,
        serialize=False,
        backtrace=True,
        diagnose=True,
        rotation=_resolve_log_option("LOG_ROTATION", "log_rotation", "50 MB"),
        retention=_resolve_log_option("LOG_RETENTION", "log_retention", "7 days"),
        compression=_resolve_log_option("LOG_COMPRESSION", "log_compression", "zip"),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    return log_path


def configure_tools_logging(script_name: str) -> Path:
    """Configure concise console sink and detailed file sink for tools scripts."""
    logger.remove()
    _install_stdlib_logging_bridge()
    logger.configure(patcher=cast(Any, _redact_record))
    logger.add(
        _console_stream(),
        level=_resolve_console_log_level(),
        enqueue=False,
        serialize=False,
        backtrace=False,
        diagnose=False,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    return add_tools_file_sink(script_name)


def add_reporting_api_sink(reporting_client: Any, level: str = "WARNING") -> int | None:
    """Attach optional sink that forwards Loguru records to Reporting API."""
    client = reporting_client
    endpoint = str(getattr(client, "log_endpoint", "") or "").strip()
    enabled = bool(getattr(client, "enabled", False))
    base_url = str(getattr(client, "base_url", "") or "").strip()
    if not enabled or not base_url or not endpoint:
        return None

    normalized_level = _normalize_log_level(level, default="WARNING")

    def _sink(message: Any) -> None:
        record = cast(dict[str, Any], getattr(message, "record", {}))
        if not isinstance(record, dict):
            return
        extra = record.get("extra")
        if not isinstance(extra, dict):
            extra = {}
        if bool(extra.get("_skip_remote_log", False)):
            return

        event_type = str(record.get("message", "") or "")
        metadata = {
            "tester": str(extra.get("tester", "") or ""),
            "run_note": str(extra.get("run_note", "") or ""),
            "hostname": str(extra.get("hostname", "") or ""),
            "worker_id": str(extra.get("worker_id", "") or ""),
            "browser": str(extra.get("browser", "") or ""),
        }
        event_extra = {
            "event": event_type,
            "module": str(record.get("module", "") or ""),
            "function": str(record.get("function", "") or ""),
            "line": int(record.get("line", 0) or 0),
        }
        level_obj = record.get("level")
        level_name = str(getattr(level_obj, "name", "INFO") or "INFO")

        client.log_event(
            level=level_name,
            message=event_type,
            run_id=str(extra.get("run_id", "") or ""),
            nodeid=str(extra.get("nodeid", "") or ""),
            metadata=metadata,
            timestamp=str(record.get("time", "") or ""),
            extra=event_extra,
        )

    return cast(
        int,
        logger.add(
            _sink,
            level=normalized_level,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            catch=True,
        ),
    )


def bind_test_context(nodeid: str):
    """Tag the logger with a pytest nodeid so subsequent logs carry the test context."""
    return logger.bind(nodeid=nodeid)
