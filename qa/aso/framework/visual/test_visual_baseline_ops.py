from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from tools.visual.baseline_ops.executor import execute_ops, plan_copy_ops
from tools.visual.baseline_ops.lifecycle_ops import _clean_empty_directories, _is_empty_directory
from tools.visual.baseline_ops.manifest import write_manifest
from tools.visual.baseline_ops.types import FileEntry
from tools.visual.baseline_ops.version_copy import apply_version_copy

pytestmark = [pytest.mark.aso]


def _env() -> SimpleNamespace:
    return SimpleNamespace(
        visual_cache_dir=".visual_cache",
        visual_baseline_profile="test-ref",
        visual_minio_endpoint="",
        visual_minio_bucket="visual-baselines",
        visual_minio_access_key="",
        visual_minio_secret_key="",
        visual_minio_secure=False,
    )


def test_plan_and_execute_ops_handles_copy_skip_and_remove(tmp_path: Path) -> None:
    source_copy = tmp_path / "source_copy.png"
    source_skip = tmp_path / "source_skip.png"
    source_copy.write_bytes(b"new-bytes")
    source_skip.write_bytes(b"same")

    target_copy = tmp_path / "target_copy.png"
    target_skip = tmp_path / "target_skip.png"
    target_skip.write_bytes(b"oldx")
    target_remove = tmp_path / "target_remove.png"
    target_remove.write_bytes(b"remove")

    source_paths = {
        "suite/test-ref/latest/copy.png": source_copy,
        "suite/test-ref/latest/skip.png": source_skip,
    }
    target_paths = {
        "suite/test-ref/latest/copy.png": target_copy,
        "suite/test-ref/latest/skip.png": target_skip,
        "suite/test-ref/latest/remove.png": target_remove,
    }

    ops = plan_copy_ops(source_paths, target_paths, prune_missing=True)
    summary = execute_ops(ops, dry_run=False)

    assert summary.copied == 1
    assert summary.skipped == 1
    assert summary.removed == 1
    assert summary.failed == 0
    assert target_copy.read_bytes() == b"new-bytes"
    assert not target_remove.exists()


def test_write_manifest_includes_total_and_suite_sizes(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    files = {
        "suite-a/test-ref/v1/a.png": FileEntry(
            object_key="suite-a/test-ref/v1/a.png",
            absolute_path=tmp_path / "a.png",
            size_bytes=100,
            suite_id="suite-a",
        ),
        "suite-b/test-ref/v1/b.png": FileEntry(
            object_key="suite-b/test-ref/v1/b.png",
            absolute_path=tmp_path / "b.png",
            size_bytes=300,
            suite_id="suite-b",
        ),
    }

    write_manifest(
        manifest_path=manifest_path,
        profile="test-ref",
        version="v1",
        source_version="latest",
        files=files,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["file_count"] == 2
    assert payload["total_size_bytes"] == 400
    assert payload["total_size_mib"] == round(400 / (1024**2), 2)
    suites = {item["suite_id"]: item for item in payload["suites"]}
    assert suites["suite-a"]["suite_size_bytes"] == 100
    assert suites["suite-b"]["suite_size_bytes"] == 300


def test_apply_version_copy_promotes_candidates_to_latest_and_writes_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    baseline_file = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "candidates" / "a.png"
    cache_file = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "candidates" / "a.png"
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_bytes(b"candidate")
    cache_file.write_bytes(b"candidate")

    import tools.visual.baseline_ops.version_copy as versioning

    monkeypatch.setattr(versioning, "repo_root", lambda: repo_root)

    result = apply_version_copy(
        cast(Any, _env()),
        profile="test-ref",
        from_version="candidates",
        to_version="latest",
        suites={"suite-1"},
        dry_run=False,
        prune_missing=False,
        with_minio=False,
        minio_credentials=None,
        write_manifest_file=True,
    )

    latest_local = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "latest" / "a.png"
    latest_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "latest" / "a.png"
    assert latest_local.is_file()
    assert latest_cache.is_file()
    assert latest_local.read_bytes() == b"candidate"
    assert latest_cache.read_bytes() == b"candidate"
    assert result.local_summary.copied == 1
    assert result.cache_summary.copied == 1
    assert result.manifest_path is not None


def test_apply_version_copy_prunes_latest_files_missing_in_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"

    source_local = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "candidates" / "keep.png"
    source_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "candidates" / "keep.png"
    source_local.parent.mkdir(parents=True, exist_ok=True)
    source_cache.parent.mkdir(parents=True, exist_ok=True)
    source_local.write_bytes(b"keep")
    source_cache.write_bytes(b"keep")

    stale_local = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "latest" / "stale.png"
    stale_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "latest" / "stale.png"
    stale_local.parent.mkdir(parents=True, exist_ok=True)
    stale_cache.parent.mkdir(parents=True, exist_ok=True)
    stale_local.write_bytes(b"stale")
    stale_cache.write_bytes(b"stale")

    import tools.visual.baseline_ops.version_copy as versioning

    monkeypatch.setattr(versioning, "repo_root", lambda: repo_root)

    result = apply_version_copy(
        cast(Any, _env()),
        profile="test-ref",
        from_version="candidates",
        to_version="latest",
        suites={"suite-1"},
        dry_run=False,
        prune_missing=True,
        with_minio=False,
        minio_credentials=None,
        write_manifest_file=False,
    )

    kept_local = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "latest" / "keep.png"
    kept_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "latest" / "keep.png"

    assert kept_local.is_file()
    assert kept_cache.is_file()
    assert not stale_local.exists()
    assert not stale_cache.exists()
    assert result.local_summary.removed == 1
    assert result.cache_summary.removed == 1


def test_apply_version_copy_uses_cache_source_when_requested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    source_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "latest" / "from-cache.png"
    source_cache.parent.mkdir(parents=True, exist_ok=True)
    source_cache.write_bytes(b"cache-bytes")

    import tools.visual.baseline_ops.version_copy as versioning

    monkeypatch.setattr(versioning, "repo_root", lambda: repo_root)

    result = apply_version_copy(
        cast(Any, _env()),
        profile="test-ref",
        from_version="latest",
        to_version="2026-03-06",
        suites={"suite-1"},
        source="cache",
        dry_run=False,
        prune_missing=False,
        with_minio=False,
        minio_credentials=None,
        write_manifest_file=False,
    )

    target_local = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "2026-03-06" / "from-cache.png"
    target_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "2026-03-06" / "from-cache.png"

    assert target_local.is_file()
    assert target_cache.is_file()
    assert target_local.read_bytes() == b"cache-bytes"
    assert target_cache.read_bytes() == b"cache-bytes"
    assert result.local_summary.copied == 1
    assert result.cache_summary.copied == 1


def test_apply_version_copy_auto_uses_baseline_for_cache_when_source_cache_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    source_local = repo_root / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "latest" / "from-local.png"
    source_local.parent.mkdir(parents=True, exist_ok=True)
    source_local.write_bytes(b"local-only")

    import tools.visual.baseline_ops.version_copy as versioning

    monkeypatch.setattr(versioning, "repo_root", lambda: repo_root)

    result = apply_version_copy(
        cast(Any, _env()),
        profile="test-ref",
        from_version="latest",
        to_version="2026-03-06",
        suites={"suite-1"},
        source="auto",
        dry_run=False,
        prune_missing=False,
        with_minio=False,
        minio_credentials=None,
        write_manifest_file=False,
    )

    target_cache = repo_root / ".visual_cache" / "suite-1" / "test-ref" / "2026-03-06" / "from-local.png"
    assert target_cache.is_file()
    assert target_cache.read_bytes() == b"local-only"
    assert result.cache_summary.copied == 1


def test_sync_minio_falls_back_to_local_upload_when_source_key_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tools.visual.baseline_ops.version_copy as versioning

    source_path = tmp_path / "source.png"
    source_path.write_bytes(b"png-bytes")
    source_key = "suite-1/test-ref/latest/a.png"
    source_entries = {
        source_key: FileEntry(
            object_key=source_key,
            absolute_path=source_path,
            size_bytes=source_path.stat().st_size,
            suite_id="suite-1",
        )
    }

    copied_calls: list[tuple[str, str]] = []
    upload_calls: list[tuple[Path, str]] = []

    class _FakeMinioOps:
        def __init__(self, *_a, **_k) -> None:
            pass

        def copy_object(self, source_key: str, target_key: str) -> None:
            copied_calls.append((source_key, target_key))
            raise Exception("S3 operation failed; code: NoSuchKey")

        def upload_file(self, local_path: Path, target_key: str) -> None:
            upload_calls.append((local_path, target_key))

        def list_keys(self, _prefix: str) -> set[str]:
            return set()

    monkeypatch.setattr(versioning, "MinioOps", _FakeMinioOps)

    copied = versioning._sync_minio(
        cast(Any, _env()),
        source_entries=source_entries,
        to_version="2026-03-05",
        dry_run=False,
        prune_missing=False,
        credentials=None,
        profile="test-ref",
        suites={"suite-1"},
    )

    assert copied == 1
    assert copied_calls == [(source_key, "suite-1/test-ref/2026-03-05/a.png")]
    assert upload_calls == [(source_path, "suite-1/test-ref/2026-03-05/a.png")]


def test_sync_minio_does_not_fallback_upload_for_non_missing_source_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tools.visual.baseline_ops.version_copy as versioning

    source_path = tmp_path / "source.png"
    source_path.write_bytes(b"png-bytes")
    source_key = "suite-1/test-ref/latest/a.png"
    source_entries = {
        source_key: FileEntry(
            object_key=source_key,
            absolute_path=source_path,
            size_bytes=source_path.stat().st_size,
            suite_id="suite-1",
        )
    }

    upload_calls: list[tuple[Path, str]] = []

    class _FakeMinioOps:
        def __init__(self, *_a, **_k) -> None:
            pass

        def copy_object(self, _source_key: str, _target_key: str) -> None:
            raise Exception("S3 operation failed; code: AccessDenied")

        def upload_file(self, local_path: Path, target_key: str) -> None:
            upload_calls.append((local_path, target_key))

        def list_keys(self, _prefix: str) -> set[str]:
            return set()

    monkeypatch.setattr(versioning, "MinioOps", _FakeMinioOps)

    copied = versioning._sync_minio(
        cast(Any, _env()),
        source_entries=source_entries,
        to_version="2026-03-05",
        dry_run=False,
        prune_missing=False,
        credentials=None,
        profile="test-ref",
        suites={"suite-1"},
    )

    assert copied == 0
    assert upload_calls == []


def test_is_empty_directory_returns_true_for_empty_dir(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert _is_empty_directory(empty_dir) is True


def test_is_empty_directory_returns_false_for_non_empty_dir(tmp_path: Path) -> None:
    non_empty_dir = tmp_path / "non_empty"
    non_empty_dir.mkdir()
    (non_empty_dir / "file.txt").write_text("content")
    assert _is_empty_directory(non_empty_dir) is False


def test_is_empty_directory_returns_false_for_non_existent_path(tmp_path: Path) -> None:
    assert _is_empty_directory(tmp_path / "does_not_exist") is False


def test_is_empty_directory_returns_false_for_file(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")
    assert _is_empty_directory(file_path) is False


def test_clean_empty_directories_removes_empty_version_dirs(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    version_dir = root / "suite-1" / "test-ref" / "v1"
    version_dir.mkdir(parents=True)

    removed, failed = _clean_empty_directories(
        root,
        profile="test-ref",
        version="v1",
        suites={"suite-1"},
        dry_run=False,
    )

    assert removed >= 1
    assert failed == 0
    assert not version_dir.exists()


def test_clean_empty_directories_removes_empty_profile_dir(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    version_dir = root / "suite-1" / "test-ref" / "v1"
    version_dir.mkdir(parents=True)

    removed, failed = _clean_empty_directories(
        root,
        profile="test-ref",
        version="v1",
        suites={"suite-1"},
        dry_run=False,
    )

    profile_dir = root / "suite-1" / "test-ref"
    assert removed >= 1
    assert failed == 0
    assert not profile_dir.exists()


def test_clean_empty_directories_preserves_non_empty_dirs(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    version_dir = root / "suite-1" / "test-ref" / "v1"
    version_dir.mkdir(parents=True)
    (version_dir / "keep.png").write_bytes(b"png")

    removed, failed = _clean_empty_directories(
        root,
        profile="test-ref",
        version="v1",
        suites={"suite-1"},
        dry_run=False,
    )

    assert removed == 0
    assert failed == 0
    assert version_dir.exists()


def test_clean_empty_directories_dry_run_does_not_remove(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    version_dir = root / "suite-1" / "test-ref" / "v1"
    version_dir.mkdir(parents=True)

    removed, failed = _clean_empty_directories(
        root,
        profile="test-ref",
        version="v1",
        suites={"suite-1"},
        dry_run=True,
    )

    assert removed == 1
    assert failed == 0
    assert version_dir.exists()


def test_clean_empty_directories_handles_all_versions(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    v1_dir = root / "suite-1" / "test-ref" / "v1"
    v2_dir = root / "suite-1" / "test-ref" / "v2"
    v1_dir.mkdir(parents=True)
    v2_dir.mkdir(parents=True)

    removed, failed = _clean_empty_directories(
        root,
        profile="test-ref",
        version=None,
        suites={"suite-1"},
        dry_run=False,
    )

    assert removed >= 2
    assert failed == 0
    assert not v1_dir.exists()
    assert not v2_dir.exists()


def test_clean_empty_directories_filters_by_suite(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    suite1_dir = root / "suite-1" / "test-ref" / "v1"
    suite2_dir = root / "suite-2" / "test-ref" / "v1"
    suite1_dir.mkdir(parents=True)
    suite2_dir.mkdir(parents=True)

    removed, failed = _clean_empty_directories(
        root,
        profile="test-ref",
        version="v1",
        suites={"suite-1"},
        dry_run=False,
    )

    assert removed >= 1
    assert failed == 0
    assert not suite1_dir.exists()
    assert suite2_dir.exists()
