from __future__ import annotations

from loguru import logger

from .context import ChallengeEntry, ReportServerContext
from .http import _build_handler
from .paths import (
    _discover_visual_run_dirs,
    _resolve_actual_png,
    _resolve_report_dir,
    _run_id_from_visual_dir,
    _safe_run_id_or_error,
)
from .reports import _list_reports_payload, _read_results_rows, _report_summary
from .services.pdf import _generate_bug_pdf
from .state import LOCK_TTL_SECONDS, _acquire_lock, _treat_reporting_disabled_as_success

__all__ = [
    "ChallengeEntry",
    "LOCK_TTL_SECONDS",
    "ReportServerContext",
    "_acquire_lock",
    "_build_handler",
    "_discover_visual_run_dirs",
    "_generate_bug_pdf",
    "_list_reports_payload",
    "_read_results_rows",
    "_report_summary",
    "_resolve_actual_png",
    "_resolve_report_dir",
    "_run_id_from_visual_dir",
    "_safe_run_id_or_error",
    "_treat_reporting_disabled_as_success",
    "logger",
]
