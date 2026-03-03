from __future__ import annotations

from pathlib import Path

from .types import FileEntry


def scan_local_version(
    baseline_root: Path,
    *,
    profile: str,
    version: str,
    suites: set[str] | None = None,
) -> dict[str, FileEntry]:
    entries: dict[str, FileEntry] = {}
    if not baseline_root.is_dir():
        return entries

    for suite_dir in sorted(path for path in baseline_root.iterdir() if path.is_dir()):
        suite_id = suite_dir.name
        if suites and suite_id not in suites:
            continue
        version_dir = suite_dir / profile / version
        if not version_dir.is_dir():
            continue
        for path in sorted(version_dir.rglob("*.png")):
            if not path.is_file():
                continue
            object_key = path.relative_to(baseline_root).as_posix()
            try:
                size_bytes = path.stat().st_size
            except OSError:
                continue
            entries[object_key] = FileEntry(
                object_key=object_key,
                absolute_path=path,
                size_bytes=size_bytes,
                suite_id=suite_id,
            )
    return entries


def list_local_versions(baseline_root: Path, *, profile: str, suites: set[str] | None = None) -> list[str]:
    versions: set[str] = set()
    if not baseline_root.is_dir():
        return []

    for suite_dir in sorted(path for path in baseline_root.iterdir() if path.is_dir()):
        suite_id = suite_dir.name
        if suites and suite_id not in suites:
            continue
        profile_dir = suite_dir / profile
        if not profile_dir.is_dir():
            continue
        for version_dir in sorted(path for path in profile_dir.iterdir() if path.is_dir()):
            versions.add(version_dir.name)

    return sorted(versions)
