from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from tools.visual.baseline_ops.retention import RetentionEntry, _select_keys_to_remove, apply_retention

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


def test_select_keys_to_remove_respects_candidates_ttl_and_keep_versions() -> None:
    now = datetime.now(timezone.utc)
    entries = [
        RetentionEntry("suite/test-ref/candidates/old.png", "suite", "candidates", now - timedelta(days=10)),
        RetentionEntry("suite/test-ref/candidates/new.png", "suite", "candidates", now - timedelta(days=1)),
        RetentionEntry("suite/test-ref/v1/a.png", "suite", "v1", now - timedelta(days=30)),
        RetentionEntry("suite/test-ref/v2/a.png", "suite", "v2", now - timedelta(days=20)),
        RetentionEntry("suite/test-ref/v3/a.png", "suite", "v3", now - timedelta(days=10)),
        RetentionEntry("suite/test-ref/latest/a.png", "suite", "latest", now),
    ]

    keys = _select_keys_to_remove(
        entries,
        candidates_cutoff_utc=now - timedelta(days=7),
        keep_versions=2,
    )

    assert "suite/test-ref/candidates/old.png" in keys
    assert "suite/test-ref/candidates/new.png" not in keys
    assert "suite/test-ref/v1/a.png" in keys
    assert "suite/test-ref/v2/a.png" not in keys
    assert "suite/test-ref/v3/a.png" not in keys
    assert "suite/test-ref/latest/a.png" not in keys


def test_apply_retention_removes_from_local_and_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"

    old_candidates = repo / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "candidates" / "old.png"
    new_candidates = repo / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "candidates" / "new.png"
    old_version = repo / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "v1" / "a.png"
    keep_version = repo / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "v2" / "a.png"
    latest = repo / "qa" / "visual" / "baselines" / "suite-1" / "test-ref" / "latest" / "a.png"

    for path, payload in [
        (old_candidates, b"old"),
        (new_candidates, b"new"),
        (old_version, b"v1"),
        (keep_version, b"v2"),
        (latest, b"latest"),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    old_cache = repo / ".visual_cache" / "suite-1" / "test-ref" / "candidates" / "old.png"
    old_cache.parent.mkdir(parents=True, exist_ok=True)
    old_cache.write_bytes(b"old")

    old_mtime = datetime.now(timezone.utc) - timedelta(days=9)
    ts = old_mtime.timestamp()
    for path in [old_candidates, old_cache]:
        path.touch()
        path.chmod(0o644)
        import os

        os.utime(path, (ts, ts))

    import tools.visual.baseline_ops.retention as retention

    monkeypatch.setattr(retention, "repo_root", lambda: repo)

    summary = apply_retention(
        cast(Any, _env()),
        profile="test-ref",
        suites={"suite-1"},
        ttl_candidates_days=7,
        keep_versions=1,
        dry_run=False,
        with_minio=False,
        minio_credentials=None,
    )

    assert summary.removed_local_files >= 2
    assert summary.removed_cache_files >= 1
    assert not old_candidates.exists()
    assert not old_cache.exists()
    assert not old_version.exists()
    assert new_candidates.exists()
    assert keep_version.exists()
    assert latest.exists()
