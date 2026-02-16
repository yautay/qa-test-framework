from __future__ import annotations

from pathlib import Path

from framework.env import RuntimeEnv


class BaselineStore:
    def __init__(self, env: RuntimeEnv, repo_root: Path) -> None:
        self._env = env
        self._repo_root = repo_root
        self._cache_dir = (repo_root / env.visual_cache_dir).resolve()

    def baseline_key(self, suite_id: str, scenario_id: str, viewport: str, browser: str) -> str:
        file_name = f"{scenario_id}__{viewport}__{browser}.png"
        return (
            f"{suite_id.strip('/')}/{self._env.visual_baseline_profile}/"
            f"{self._env.visual_baseline_version}/{file_name}"
        )

    def local_cache_path(self, object_key: str) -> Path:
        return self._cache_dir / object_key

    def resolve_baseline(self, suite_id: str, scenario_id: str, viewport: str,
                         browser: str) -> Path | None:
        object_key = self.baseline_key(suite_id, scenario_id, viewport, browser)
        local_path = self.local_cache_path(object_key)
        if local_path.is_file():
            return local_path

        if self._env.visual_baseline_provider == "local":
            local_fallback = self._repo_root / "qa" / "visual" / "baselines" / object_key
            if local_fallback.is_file():
                return local_fallback
            return None

        if self._env.visual_baseline_provider == "minio" and self._download_minio_object(object_key,
                                                                                         local_path):
            return local_path
        return None

    def store_baseline(self, suite_id: str, scenario_id: str, viewport: str, browser: str,
                       source: Path) -> Path:
        object_key = self.baseline_key(suite_id, scenario_id, viewport, browser)
        target = self.local_cache_path(object_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        if self._env.visual_baseline_provider == "minio":
            self._upload_minio_object(object_key, target)
        return target

    def _download_minio_object(self, object_key: str, local_path: Path) -> bool:
        if not self._env.visual_minio_endpoint:
            return False
        try:
            from minio import Minio
        except Exception:
            return False

        client = Minio(
            self._env.visual_minio_endpoint,
            access_key=self._env.visual_minio_access_key,
            secret_key=self._env.visual_minio_secret_key,
            secure=self._env.visual_minio_secure,
        )
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            client.fget_object(self._env.visual_minio_bucket, object_key, str(local_path))
            return local_path.is_file()
        except Exception:
            return False

    def _upload_minio_object(self, object_key: str, local_path: Path) -> None:
        if not self._env.visual_minio_endpoint:
            return
        try:
            from minio import Minio
        except Exception:
            return
        client = Minio(
            self._env.visual_minio_endpoint,
            access_key=self._env.visual_minio_access_key,
            secret_key=self._env.visual_minio_secret_key,
            secure=self._env.visual_minio_secure,
        )
        try:
            if not client.bucket_exists(self._env.visual_minio_bucket):
                client.make_bucket(self._env.visual_minio_bucket)
            client.fput_object(self._env.visual_minio_bucket, object_key, str(local_path))
        except Exception:
            return
