from __future__ import annotations

"""Loguru helpers that bind execution context and channel logs to stdout + file."""

import os
import socket
import sys
from pathlib import Path

from loguru import logger

import settings_cli


def _resolve_console_log_level() -> str:
    """Normalize console log level from env/settings, falling back to INFO."""

    value = os.getenv("CONSOLE_LOG_LEVEL", getattr(settings_cli, "console_log_level", "INFO"))
    normalized = str(value).strip().upper()
    allowed = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
    if normalized in allowed:
        return normalized
    return "INFO"


def configure_logging(
    run_log_file: Path,
    run_id: str,
    browser: str,
    worker_id: str,
    git_user_name: str | None,
    git_user_email: str | None,
) -> None:
    """Prepare console + file sinks and attach tracer metadata for Loguru."""

    logger.remove()
    run_log_file.parent.mkdir(parents=True, exist_ok=True)
    base_extra = {
        "run_id": run_id,
        "hostname": socket.gethostname(),
        "browser": browser,
        "worker_id": worker_id,
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
    }
    logger.configure(extra=base_extra)
    logger.add(
        sys.stdout,
        level=_resolve_console_log_level(),
        serialize=True,
        enqueue=True,
    )
    logger.add(
        str(run_log_file),
        level="DEBUG",
        serialize=True,
        enqueue=True,
    )


def bind_test_context(nodeid: str):
    """Tag the logger with a pytest nodeid so subsequent logs carry the test context."""

    return logger.bind(nodeid=nodeid)
