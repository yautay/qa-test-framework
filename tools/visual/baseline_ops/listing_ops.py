from __future__ import annotations

from pathlib import Path

from framework.env import RuntimeEnv

from .minio_ops import MinioOps
from .models import VersionStats
from .paths import local_baseline_root, parse_object_key, repo_root
from .scanner import list_local_versions as _list_local_versions


def list_local_versions(env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> list[str]:
    root = local_baseline_root(repo_root())
    return _list_local_versions(root, profile=profile, suites=suites)


def list_minio_versions(env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> list[str]:
    ops = MinioOps(env)
    versions: set[str] = set()
    suite_list = sorted(suites) if suites else [""]

    for suite_id in suite_list:
        prefix = f"{suite_id}/{profile}/" if suite_id else ""
        for obj in ops.list_objects(prefix):
            try:
                parsed_suite, parsed_profile, version, _rest = parse_object_key(obj.object_key)
            except ValueError:
                continue
            if parsed_profile != profile:
                continue
            if suites and parsed_suite not in suites:
                continue
            versions.add(version)

    return sorted(versions)


def local_version_stats(env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> dict[str, VersionStats]:
    root = local_baseline_root(repo_root())
    stats: dict[str, VersionStats] = {}
    if not root.is_dir():
        return stats

    for suite_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        suite_id = suite_dir.name
        if suites and suite_id not in suites:
            continue
        profile_dir = suite_dir / profile
        if not profile_dir.is_dir():
            continue
        for version_dir in sorted(path for path in profile_dir.iterdir() if path.is_dir()):
            version = version_dir.name
            files = 0
            total_bytes = 0
            for png in version_dir.rglob("*.png"):
                if not png.is_file():
                    continue
                files += 1
                total_bytes += _safe_size(png)
            prev = stats.get(version, VersionStats(file_count=0, total_bytes=0))
            stats[version] = VersionStats(
                file_count=prev.file_count + files,
                total_bytes=prev.total_bytes + total_bytes,
            )

    return dict(sorted(stats.items()))


def minio_version_stats(env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> dict[str, VersionStats]:
    ops = MinioOps(env)
    stats: dict[str, VersionStats] = {}
    suite_list = sorted(suites) if suites else [""]

    for suite_id in suite_list:
        prefix = f"{suite_id}/{profile}/" if suite_id else ""
        for obj in ops.list_objects(prefix):
            try:
                parsed_suite, parsed_profile, version, _rest = parse_object_key(obj.object_key)
            except ValueError:
                continue
            if parsed_profile != profile:
                continue
            if suites and parsed_suite not in suites:
                continue
            prev = stats.get(version, VersionStats(file_count=0, total_bytes=0))
            stats[version] = VersionStats(
                file_count=prev.file_count + 1,
                total_bytes=prev.total_bytes + obj.size_bytes,
            )

    return dict(sorted(stats.items()))


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
