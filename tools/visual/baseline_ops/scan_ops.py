from __future__ import annotations

from pathlib import Path

from .minio_ops import MinioObject, MinioOps
from .paths import parse_object_key
from .types import FileEntry


def scan_cache_version(
    cache_root: Path,
    *,
    profile: str,
    version: str,
    suites: set[str] | None,
) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not cache_root.is_dir():
        return out
    for suite_dir in sorted(path for path in cache_root.iterdir() if path.is_dir()):
        suite_id = suite_dir.name
        if suites and suite_id not in suites:
            continue
        version_dir = suite_dir / profile / version
        if not version_dir.is_dir():
            continue
        for path in sorted(version_dir.rglob("*.png")):
            out[path.relative_to(cache_root).as_posix()] = path
    return out


def scan_local_profile_files(
    root: Path,
    *,
    profile: str,
    version: str | None,
    suites: set[str] | None,
) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not root.is_dir():
        return out
    for suite_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        suite_id = suite_dir.name
        if suites and suite_id not in suites:
            continue
        profile_dir = suite_dir / profile
        if not profile_dir.is_dir():
            continue
        version_dirs = (
            [profile_dir / version]
            if version is not None
            else sorted(path for path in profile_dir.iterdir() if path.is_dir())
        )
        for version_dir in version_dirs:
            if not version_dir.is_dir():
                continue
            for path in sorted(version_dir.rglob("*.png")):
                out[path.relative_to(root).as_posix()] = path
    return out


def to_file_entries(paths: dict[str, Path]) -> dict[str, FileEntry]:
    out: dict[str, FileEntry] = {}
    for object_key, absolute_path in paths.items():
        try:
            suite_id, _profile, _version, _rest = parse_object_key(object_key)
        except ValueError:
            continue
        out[object_key] = FileEntry(
            object_key=object_key,
            absolute_path=absolute_path,
            size_bytes=_safe_size(absolute_path),
            suite_id=suite_id,
        )
    return out


def scan_minio_version(
    ops: MinioOps,
    *,
    profile: str,
    version: str,
    suites: set[str] | None,
) -> dict[str, MinioObject]:
    out: dict[str, MinioObject] = {}
    prefixes = [f"{suite_id}/{profile}/{version}/" for suite_id in sorted(suites)] if suites else [""]
    for prefix in prefixes:
        for obj in ops.list_objects(prefix):
            try:
                parsed_suite, parsed_profile, parsed_version, _rest = parse_object_key(obj.object_key)
            except ValueError:
                continue
            if parsed_profile != profile or parsed_version != version:
                continue
            if suites and parsed_suite not in suites:
                continue
            out[obj.object_key] = obj
    return out


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
