from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .context import ReportServerContext


def _resolve_sync_workers(configured_workers: int | None) -> int:
    cpu = os.cpu_count() or 2
    auto_workers = min(12, max(2, cpu * 2))
    if configured_workers is None:
        return auto_workers
    try:
        requested = int(configured_workers)
    except Exception:
        return auto_workers
    if requested <= 0:
        return auto_workers
    return requested


def _generate_bug_pdf(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    bug_rows: list[tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[str, int]:
    from .services.pdf import _generate_bug_pdf as _impl

    return _impl(context=context, run_id=run_id, report_dir=report_dir, bug_rows=bug_rows)


def _build_handler(context: ReportServerContext):
    from .routes.handler import _build_handler as _impl

    return _impl(context)
