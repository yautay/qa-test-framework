from __future__ import annotations

"""
Baseline storage for visual-regression tests with pluggable providers.

This module standardizes how "baseline" images (reference screenshots) are named,
stored, and resolved. It supports:

- A **local on-disk cache** (always used) under `env.visual_cache_dir`.
- Optional **providers** for resolving/storing baselines:
  - `local`: read-only fallback to a repo directory (`qa/visual/baselines/...`).
  - `minio`: download/upload from/to a MinIO/S3-compatible object store.

Key goals:
- **Deterministic object keys** based on suite/profile/version + scenario metadata.
- **Path traversal protection** when mapping object keys to local filesystem paths.
- **Lazy initialization** of MinIO client and graceful degradation when MinIO
  configuration or library is missing.

Configuration (expected on RuntimeEnv):
- visual_cache_dir: relative path for local cache root inside `repo_root`.
- visual_baseline_provider: "local" | "minio" | empty/None.
- visual_baseline_profile: string identifying baseline profile.
- visual_baseline_version: string identifying baseline version.
- visual_minio_endpoint, visual_minio_access_key, visual_minio_secret_key,
  visual_minio_secure, visual_minio_bucket: MinIO connection settings.

Notes:
- This module does not validate that the provided baseline images are correct;
  it only manages storage/resolution.
- Network operations are best-effort: failures are logged and treated as cache
  misses (for download) or ignored (for upload).
"""

import re
import shutil
from pathlib import Path

from loguru import logger

from framework.env import RuntimeEnv

# Matches any character that is NOT an allowed safe path segment char.
# Allowed: letters, digits, dot, underscore, dash
_SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_segment(value: str) -> str:
    """
    Convert an arbitrary identifier to a safe single path segment.

    This is used to build object keys and filenames from inputs like suite IDs,
    scenario IDs, viewports, browsers, etc.

    Transformations:
    - trims whitespace
    - normalizes backslashes to forward slashes
    - strips leading/trailing slashes (prevents accidental path segments)
    - replaces any disallowed characters with "_"
    - returns "_" when the resulting segment would be empty

    Parameters
    ----------
    value:
        Any string identifier.

    Returns
    -------
    str
        Sanitized string safe to be used as a single path segment.
    """
    v = value.strip()
    v = v.replace("\\", "/")
    v = v.strip("/")  # remove path separators from ends
    v = _SAFE_SEGMENT.sub("_", v)
    return v or "_"


class BaselineStore:
    """
    Encapsulate caching and optional uploads for visual baselines.

    The store generates deterministic object keys for baseline PNG files and
    resolves them from:
    1) local cache, then (depending on provider)
    2) local repo fallback OR MinIO object store.

    Local cache is always written to on `store_baseline()`.
    """

    def __init__(self, env: RuntimeEnv, repo_root: Path) -> None:
        """
        Create a baseline store.

        Parameters
        ----------
        env:
            Runtime environment holding baseline/caching/provider configuration.
        repo_root:
            Repository root used to resolve:
            - cache directory (`repo_root / env.visual_cache_dir`)
            - local provider fallback (`repo_root / qa/visual/baselines`)
        """
        self._env = env
        self._repo_root = repo_root
        self._cache_dir = (repo_root / env.visual_cache_dir).resolve()
        self._minio_client = None  # lazy init

    def baseline_key(
        self,
        suite_id: str,
        scenario_id: str,
        viewport: str,
        browser: str,
        *,
        version_override: str | None = None,
    ) -> str:
        """
        Build a deterministic object key for a baseline image.

        The resulting key layout is:

            {suite}/{profile}/{version}/{scenario}__{viewport}__{browser}.png

        Where each part is sanitized to avoid unsafe path characters.

        Parameters
        ----------
        suite_id:
            Logical test suite identifier.
        scenario_id:
            Identifier of the scenario/test case.
        viewport:
            Viewport label (e.g. "1366x768", "iphone-13").
        browser:
            Browser label (e.g. "chromium", "firefox").
        version_override:
            Optional baseline version used only for this key generation.
            When omitted, `env.visual_baseline_version` is used.

        Returns
        -------
        str
            Object key relative to cache root / bucket root.
        """
        file_name = f"{_safe_segment(scenario_id)}__{_safe_segment(viewport)}__{_safe_segment(browser)}.png"
        suite = _safe_segment(suite_id)
        profile = _safe_segment(self._env.visual_baseline_profile)
        version_raw = version_override if version_override is not None else self._env.visual_baseline_version
        version = _safe_segment(version_raw)
        return f"{suite}/{profile}/{version}/{file_name}"

    def local_cache_path(self, object_key: str) -> Path:
        """
        Map an object key to a local cache path safely.

        Security:
        - Resolves the candidate path and verifies it is contained within
          `self._cache_dir`. This prevents path traversal such as:
          "../../etc/passwd" or absolute paths.

        Parameters
        ----------
        object_key:
            Object key returned by `baseline_key()`.

        Returns
        -------
        Path
            Absolute path under the local cache directory.

        Raises
        ------
        ValueError
            If the resolved path escapes the cache directory.
        """
        # Prevent path traversal by normalizing and verifying containment
        candidate = (self._cache_dir / object_key).resolve()
        try:
            candidate.relative_to(self._cache_dir)
        except ValueError:
            raise ValueError(f"Unsafe object key outside cache dir: {object_key!r}") from None
        return candidate

    def local_provider_path(self, object_key: str) -> Path:
        """Map an object key to repo local-baseline path safely.

        Local provider baselines live under `qa/visual/baselines` in repo root.
        The same path traversal protection as cache mapping is applied.
        """

        provider_root = (self._repo_root / "qa" / "visual" / "baselines").resolve()
        candidate = (provider_root / object_key).resolve()
        try:
            candidate.relative_to(provider_root)
        except ValueError:
            raise ValueError(f"Unsafe object key outside local provider dir: {object_key!r}") from None
        return candidate

    def resolve_baseline(self, suite_id: str, scenario_id: str, viewport: str, browser: str) -> Path | None:
        """
        Resolve an existing baseline image for a given scenario.

        Resolution order:
        1) Local cache (`env.visual_cache_dir`)
        2) Provider-specific fallback:
           - "local": repo fallback path under `qa/visual/baselines`
           - "minio": download object to local cache

        If provider is unset/unknown, only the local cache is used.

        Parameters
        ----------
        suite_id, scenario_id, viewport, browser:
            Components used to build the baseline key.

        Returns
        -------
        Path | None
            Path to the resolved baseline image, or None if not found.
        """
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
        """
        Store a baseline image into the local cache and optionally upload it.

        Behavior:
        - Copies `source` to the cache location derived from the baseline key.
        - If provider == "minio", uploads the cached file to MinIO.

        Parameters
        ----------
        suite_id, scenario_id, viewport, browser:
            Components used to build the baseline key.
        source:
            Path to the image file to store (expected PNG).

        Returns
        -------
        Path
            The path of the cached baseline file.

        Raises
        ------
        ValueError
            If the computed cache path is unsafe (escapes cache dir).
        FileNotFoundError
            If `source` does not exist. (Raised by copyfile)
        """
        object_key = self.baseline_key(suite_id, scenario_id, viewport, browser)
        target = self.local_cache_path(object_key)

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(target))

        provider = (self._env.visual_baseline_provider or "").strip().lower()
        if provider == "minio":
            self._upload_minio_object(object_key, target)

        return target

    def store_local_baseline(
        self,
        suite_id: str,
        scenario_id: str,
        viewport: str,
        browser: str,
        source: Path,
        *,
        version_override: str | None = None,
    ) -> Path:
        """Store baseline in repo local provider and cache.

        This method is intended for explicit baseline approval flows where the
        selected TEST image should become a new local REF candidate.

        Parameters
        ----------
        version_override:
            Optional baseline version override for write-only flows.
            Useful when approval should write to a separate lane (e.g. "candidates")
            while normal REF resolution still uses the default configured version.
        """

        object_key = self.baseline_key(
            suite_id,
            scenario_id,
            viewport,
            browser,
            version_override=version_override,
        )
        local_target = self.local_provider_path(object_key)
        cache_target = self.local_cache_path(object_key)

        local_target.parent.mkdir(parents=True, exist_ok=True)
        cache_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(local_target))
        shutil.copyfile(str(source), str(cache_target))
        return local_target

    def _get_minio_client(self):
        """
        Lazily create and cache a MinIO client.

        Returns None when:
        - MinIO endpoint is not configured, or
        - the `minio` Python library is not available.

        Returns
        -------
        Minio | None
            Instance of `minio.Minio` or None if unavailable.
        """
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
        """
        Download an object from MinIO into the local cache.

        The download is best-effort:
        - returns False if MinIO client is unavailable or any exception occurs.
        - logs a warning with exception details on failure.

        Parameters
        ----------
        object_key:
            Object key inside the MinIO bucket.
        local_path:
            Destination path in local cache.

        Returns
        -------
        bool
            True if the file exists after download, otherwise False.
        """
        client = self._get_minio_client()
        if client is None:
            return False

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            client.fget_object(self._env.visual_minio_bucket, object_key, str(local_path))
            return local_path.is_file()
        except Exception as exc:
            error_code = str(getattr(exc, "code", "") or "")
            if error_code == "NoSuchKey":
                logger.warning(
                    "minio baseline object missing",
                    bucket=self._env.visual_minio_bucket,
                    key=object_key,
                    path=str(local_path),
                    code=error_code,
                )
                return False

            logger.opt(exception=True).warning(
                "minio download failed",
                bucket=self._env.visual_minio_bucket,
                key=object_key,
                path=str(local_path),
            )
            return False

    def _upload_minio_object(self, object_key: str, local_path: Path) -> None:
        """
        Upload a local cached baseline image to MinIO.

        Upload is best-effort:
        - does nothing if MinIO client is unavailable
        - logs a warning with exception details on failure

        Behavior:
        - Ensures the bucket exists (creates it if missing).
        - Uploads `local_path` to the bucket at `object_key`.

        Parameters
        ----------
        object_key:
            Object key inside the MinIO bucket.
        local_path:
            Source file on disk to upload.
        """
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
