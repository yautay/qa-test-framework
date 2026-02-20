from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from framework.visual.baseline_store import BaselineStore

pytestmark = [pytest.mark.aso]


def _env(*, provider: str = "local") -> SimpleNamespace:
    return SimpleNamespace(
        visual_cache_dir=".visual_cache",
        visual_baseline_provider=provider,
        visual_baseline_profile="test-ref",
        visual_baseline_version="latest",
        visual_minio_endpoint="",
        visual_minio_access_key="",
        visual_minio_secret_key="",
        visual_minio_secure=False,
        visual_minio_bucket="visual-baselines",
    )


def test_store_local_baseline_writes_to_local_provider_and_cache(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = tmp_path / "actual.png"
    source.write_bytes(b"png-bytes")

    store = BaselineStore(_env(provider="local"), repo_root)

    target = store.store_local_baseline("suite-1", "scenario-1", "fhd", "chromium", source)
    object_key = store.baseline_key("suite-1", "scenario-1", "fhd", "chromium")
    cache_path = store.local_cache_path(object_key)

    assert target.is_file()
    assert target.read_bytes() == b"png-bytes"
    assert cache_path.is_file()
    assert cache_path.read_bytes() == b"png-bytes"
    assert target == (repo_root / "qa" / "visual" / "baselines" / object_key).resolve()


def test_local_provider_path_rejects_path_traversal(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    store = BaselineStore(_env(), repo_root)

    with pytest.raises(ValueError, match="Unsafe object key"):
        store.local_provider_path("../../etc/passwd")


def test_resolve_baseline_local_provider_finds_local_baseline_file(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = tmp_path / "actual.png"
    source.write_bytes(b"png-bytes")

    store = BaselineStore(_env(provider="local"), repo_root)
    stored_local = store.store_local_baseline("suite-1", "scenario-1", "fhd", "chromium", source)

    resolved = store.resolve_baseline("suite-1", "scenario-1", "fhd", "chromium")

    assert resolved is not None
    assert resolved.read_bytes() == b"png-bytes"
    assert resolved == store.local_cache_path(store.baseline_key("suite-1", "scenario-1", "fhd", "chromium"))
    assert stored_local.is_file()


def test_resolve_baseline_prefers_cache_over_local_fallback(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    store = BaselineStore(_env(provider="local"), repo_root)
    object_key = store.baseline_key("suite-1", "scenario-1", "fhd", "chromium")
    local_fallback = store.local_provider_path(object_key)
    cache_path = store.local_cache_path(object_key)

    local_fallback.parent.mkdir(parents=True, exist_ok=True)
    local_fallback.write_bytes(b"from-local")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(b"from-cache")

    resolved = store.resolve_baseline("suite-1", "scenario-1", "fhd", "chromium")

    assert resolved == cache_path
    assert resolved.read_bytes() == b"from-cache"
