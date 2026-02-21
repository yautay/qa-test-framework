from __future__ import annotations

from pathlib import Path

import pytest

from framework.visual.report_server import _run_id_from_visual_dir, _safe_run_id_or_error

pytestmark = [pytest.mark.aso]


def test_safe_run_id_accepts_alnum_dot_dash_underscore() -> None:
    assert _safe_run_id_or_error("2026.02-18_001") == "2026.02-18_001"


@pytest.mark.parametrize("raw", ["", "../evil", "a/b", "a b", "%2Fetc"])
def test_safe_run_id_rejects_unsafe_values(raw: str) -> None:
    with pytest.raises(ValueError, match="invalid run_id"):
        _safe_run_id_or_error(raw)


def test_run_id_from_visual_dir_falls_back_to_parent_when_outside_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    report_dir = tmp_path / "custom report"
    report_dir.mkdir(parents=True)

    run_id = _run_id_from_visual_dir(repo_root, report_dir)

    assert run_id
    assert " " not in run_id
    assert "/" not in run_id
