from __future__ import annotations

from pathlib import Path

import pytest

from tools.visual.report_server import _resolve_actual_png, _resolve_report_dir

pytestmark = [pytest.mark.aso]


def test_resolve_report_dir_prefers_run_id(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    report_dir = repo_root / "artifacts" / "20260101_120000_000001" / "visual"
    report_dir.mkdir(parents=True)

    resolved = _resolve_report_dir(repo_root, report_dir=None, run_id="20260101_120000_000001")

    assert resolved == report_dir.resolve()


def test_resolve_report_dir_supports_relative_report_dir(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    report_dir = repo_root / "artifacts" / "sample" / "visual"
    report_dir.mkdir(parents=True)

    resolved = _resolve_report_dir(repo_root, report_dir="artifacts/sample/visual", run_id=None)

    assert resolved == report_dir.resolve()


def test_resolve_actual_png_accepts_file_inside_report_dir(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    actual = report_dir / "actual" / "scenario.png"
    actual.parent.mkdir(parents=True)
    actual.write_bytes(b"png-bytes")

    resolved = _resolve_actual_png(report_dir, "actual/scenario.png")

    assert resolved == actual.resolve()


def test_resolve_actual_png_rejects_path_outside_report_dir(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="outside report directory"):
        _resolve_actual_png(report_dir, "../escape.png")


def test_resolve_actual_png_rejects_non_png_files(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    wrong = report_dir / "actual" / "scenario.jpg"
    wrong.parent.mkdir(parents=True)
    wrong.write_bytes(b"jpg-bytes")

    with pytest.raises(ValueError, match="must be a .png"):
        _resolve_actual_png(report_dir, "actual/scenario.jpg")
