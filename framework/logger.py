from __future__ import annotations
import os
import socket
import sys
from pathlib import Path
from loguru import logger

import settings

"""Loguru helpers that bind execution context and channel logs to stdout + JSON file.

Best practices implemented:
- stdout: human-readable logs (no JSON) for developer ergonomics
- file: JSON logs (serialize=True) for ingestion and post-run analysis
- per-worker file logs to avoid contention/rotation races in parallel execution
- rotation/retention/compression configurable via env vars
- safe default `nodeid="(session)"` to prevent format KeyError before binding test context
"""


def _resolve_console_log_level() -> str:
    """Normalize console log level from env/settings, falling back to INFO."""
    value = os.getenv("CONSOLE_LOG_LEVEL", getattr(settings, "console_log_level", "INFO"))
    normalized = str(value).strip().upper()
    if normalized == "WARN":
        normalized = "WARNING"

    allowed = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
    return normalized if normalized in allowed else "INFO"


def _sanitize_worker_id(worker_id: str) -> str:
    """Make worker id safe for filenames."""
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in worker_id.strip())
    return safe or "w0"


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
    logger.configure(extra=base_extra)

    # Human-readable console sink
    logger.add(
        sys.stdout,
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
        rotation=os.getenv("LOG_ROTATION", "50 MB"),
        retention=os.getenv("LOG_RETENTION", "7 days"),
        compression=os.getenv("LOG_COMPRESSION", "zip"),
    )

    return log_file


def bind_test_context(nodeid: str):
    """Tag the logger with a pytest nodeid so subsequent logs carry the test context."""
    return logger.bind(nodeid=nodeid)
