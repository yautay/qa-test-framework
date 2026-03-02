from __future__ import annotations

import re
import uuid

_SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe(value: str) -> str:
    normalized = _SAFE_SEGMENT.sub("_", str(value or "").strip())
    return normalized or "_"


def build_test_id(*, suite_id: str, scenario_id: str, viewport: str, browser: str) -> str:
    return "::".join(
        [
            _safe(suite_id),
            _safe(scenario_id),
            _safe(viewport),
            _safe(browser),
        ]
    )


def build_pair_id(*, test_id: str, baseline_path: str, actual_path: str) -> str:
    base = _safe(baseline_path)
    actual = _safe(actual_path)
    return f"{_safe(test_id)}::{base}::{actual}"


def build_job_id(*, run_id: str, pair_id: str, metric: str, model: str, normalize: bool) -> str:
    seed = "|".join(
        [
            str(run_id or "").strip(),
            str(pair_id or "").strip(),
            str(metric or "").strip().lower(),
            str(model or "").strip().lower(),
            "true" if normalize else "false",
        ]
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
