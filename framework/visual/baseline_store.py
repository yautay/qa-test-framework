from __future__ import annotations

"""Store and resolve baselines with optional Minio/local providers."""

import re
import shutil
from pathlib import Path
from typing import Optional

from loguru import logger

from framework.env import RuntimeEnv

_SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_segment(value: str) -> str:
    """Convert an arbitrary identifier to a safe path segment."""
    v = value.strip()
    v = v.replace("\\", "/")
    v = v.strip("/")  # remove path separators from ends
    v = _SAFE_SEGMENT.sub("_", v)
    return v or "_"


class BaselineStore:
    """Encapsulate caching and optional uploads for visual baselines."""

    def __init__(self, env: RuntimeEnv, repo_root: Path) -> None:
        self._env = env
        self._repo_root = repo_root
        self._cache_dir = (repo_root / env.visual_cache_dir).resolve()
        self._minio_client = None  # lazy init

    def baseline_key(self, suite_id: str, scenario_id: str, viewport: str, browser: str) -> str:
        file_name = f"{_safe_segment(scenario_id)}__{_safe_segment(viewport)}__{_safe_segment(browser)}.png"
        suite = _safe_segment(suite_id)
        profile = _safe_segment(self._env.visual_baseline_profile)
        version = _safe_segment(self._env.visual_baseline_version)
        return f"{suite}/{profile}/{version}/{file_name}"

    def local_cache_path(self, object_key: str) -> Path:
        # Prevent path traversal by normalizing and verifying containment
        candidate = (self._cache_dir / object_key).resolve()
        try:
            candidate.relative_to(self._cache_dir)
        except ValueError:
            raise ValueError(f"Unsafe object key outside cache dir: {object_key!r}")
        return candidate

    def resolve_baseline(self, suite_id: str, scenario_id: str, viewport: str, browser: str) -> Path | None:
        object_key = self.baseline_key(suite_id, scenario_id, viewport, browser)
        local_path = self.local_cache_path(object_key)

        if local_path.is_file():
            return local_path

        provider = (self._env.visual_baseline_provider or "").strip().lower()

        if provider == "local":
            local_fallback = (self._repo_root / "qa" / "visual" / "baselines" / object_key).resolve()
            if local_fallback.is_file():
                return local_fallback
            return None

        if provider == "minio":
            if self._download_minio_object(object_key, local_path):
                return local_path

        return None

    def store_baseline(self, suite_id: str, scenario_id: str, viewport: str, browser: str, source: Path) -> Path:
        object_key = self.baseline_key(suite_id, scenario_id, viewport, browser)
        target = self.local_cache_path(object_key)

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(target))

        provider = (self._env.visual_baseline_provider or "").strip().lower()
        if provider == "minio":
            self._upload_minio_object(object_key, target)

        return target

    def _get_minio_client(self):
        if self._minio_client is not None:
            return self._minio_client

        if not self._env.visual_minio_endpoint:
            return None

        try:
            from minio import Minio
        except Exception:
            logger.warning("minio library not available; skipping minio operations")
            return None

        self._minio_client = Minio(
            self._env.visual_minio_endpoint,
            access_key=self._env.visual_minio_access_key,
            secret_key=self._env.visual_minio_secret_key,
            secure=self._env.visual_minio_secure,
        )
        return self._minio_client

    def _download_minio_object(self, object_key: str, local_path: Path) -> bool:
        client = self._get_minio_client()
        if client is None:
            return False

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            client.fget_object(self._env.visual_minio_bucket, object_key, str(local_path))
            return local_path.is_file()
        except Exception:
            logger.opt(exception=True).warning(
                "minio download failed",
                bucket=self._env.visual_minio_bucket,
                key=object_key,
                path=str(local_path),
            )
            return False

    def _upload_minio_object(self, object_key: str, local_path: Path) -> None:
        client = self._get_minio_client()
        if client is None:
            return

        try:
            bucket = self._env.visual_minio_bucket
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            client.fput_object(bucket, object_key, str(local_path))
        except Exception:
            logger.opt(exception=True).warning(
                "minio upload failed",
                bucket=self._env.visual_minio_bucket,
                key=object_key,
                path=str(local_path),
            )
