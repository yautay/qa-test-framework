from __future__ import annotations

import re
from pathlib import Path

import pytest

from framework.artifacts import build_run_artifacts, resolve_artifacts_base_dir

pytestmark = [pytest.mark.aso]


def test_resolve_artifacts_base_dir_anchors_relative_paths_to_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    nested_cwd = repo_root / "qa" / "visual" / "netcorner"
    nested_cwd.mkdir(parents=True)
    monkeypatch.chdir(nested_cwd)

    resolved = resolve_artifacts_base_dir("artifacts", repo_root)

    assert resolved == (repo_root / "artifacts").resolve()


def test_resolve_artifacts_base_dir_preserves_absolute_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    absolute = (tmp_path / "external-artifacts").resolve()

    resolved = resolve_artifacts_base_dir(str(absolute), repo_root)

    assert resolved == absolute


def test_resolve_artifacts_base_dir_handles_blank_value(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    resolved = resolve_artifacts_base_dir("   ", repo_root)

    assert resolved == (repo_root / "artifacts").resolve()


@pytest.mark.parametrize("base_dir", ["./artifacts", "tmp/../artifacts"])
def test_resolve_artifacts_base_dir_normalizes_relative_variants(tmp_path: Path, base_dir: str) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    resolved = resolve_artifacts_base_dir(base_dir, repo_root)

    assert resolved == (repo_root / "artifacts").resolve()


def test_build_run_artifacts_creates_expected_layout_under_resolved_base(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base_dir = resolve_artifacts_base_dir("artifacts", repo_root)

    run = build_run_artifacts(str(base_dir))

    assert run.root.parent == base_dir
    assert run.root.is_dir()
    assert run.traces.is_dir()
    assert run.screenshots.is_dir()
    assert run.videos.is_dir()
    assert run.logs.is_dir()
    assert run.failed_dom.is_dir()


def test_build_run_artifacts_writes_files_into_each_artifact_subdirectory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    base_dir = resolve_artifacts_base_dir("artifacts", repo_root)

    run = build_run_artifacts(str(base_dir))

    targets = {
        run.traces / "trace.zip": "trace-data",
        run.screenshots / "screen.png": "screen-data",
        run.videos / "video.webm": "video-data",
        run.logs / "run.log": "log-data",
        run.failed_dom / "test.failed-dom.html": "failed-dom-data",
    }

    for path, payload in targets.items():
        path.write_text(payload, encoding="utf-8")

    for path, payload in targets.items():
        assert path.exists()
        assert path.read_text(encoding="utf-8") == payload


def test_build_run_artifacts_generates_timestamp_run_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTEST_XDIST_TESTRUNUID", raising=False)
    base_dir = tmp_path / "artifacts"

    run = build_run_artifacts(str(base_dir))

    assert re.match(r"^\d{8}_\d{6}_\d{6}$", run.run_id)


def test_build_run_artifacts_creates_unique_run_directories_per_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PYTEST_XDIST_TESTRUNUID", raising=False)
    base_dir = tmp_path / "artifacts"

    first = build_run_artifacts(str(base_dir))
    second = build_run_artifacts(str(base_dir))

    assert first.run_id != second.run_id
    assert first.root != second.root
    assert first.root.parent == second.root.parent == base_dir.resolve()


def test_build_run_artifacts_uses_explicit_run_id(tmp_path: Path) -> None:
    base_dir = tmp_path / "artifacts"

    run = build_run_artifacts(str(base_dir), run_id="shared-run-id")

    assert run.run_id == "shared-run-id"
    assert run.root == (base_dir / "shared-run-id").resolve()


def test_build_run_artifacts_uses_xdist_testrunuid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base_dir = tmp_path / "artifacts"
    monkeypatch.setenv("PYTEST_XDIST_TESTRUNUID", "xdist-shared-id")

    run = build_run_artifacts(str(base_dir))

    assert run.run_id == "xdist-shared-id"
    assert run.root == (base_dir / "xdist-shared-id").resolve()
