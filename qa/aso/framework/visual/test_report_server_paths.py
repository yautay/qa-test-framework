from __future__ import annotations

from pathlib import Path

import pytest

from tools.visual.report_server import (
    _discover_visual_run_dirs,
    _resolve_actual_png,
    _resolve_report_dir,
    _run_id_from_visual_dir,
)

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


def test_discover_visual_run_dirs_lists_artifacts_visual_dirs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    visual_a = repo_root / "artifacts" / "20260101_120000_000001" / "visual"
    visual_b = repo_root / "artifacts" / "20260101_120000_000002" / "visual"
    visual_a.mkdir(parents=True)
    visual_b.mkdir(parents=True)

    discovered = _discover_visual_run_dirs(repo_root)

    assert set(discovered.keys()) == {"20260101_120000_000001", "20260101_120000_000002"}


def test_run_id_from_visual_dir_uses_artifacts_parent_name(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    report_dir = repo_root / "artifacts" / "20260101_120000_000003" / "visual"
    report_dir.mkdir(parents=True)

    run_id = _run_id_from_visual_dir(repo_root, report_dir)

    assert run_id == "20260101_120000_000003"
