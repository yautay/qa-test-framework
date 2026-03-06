from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from framework.env import RuntimeEnv

from .minio_ops import MinioCredentials, MinioObject, MinioOps
from .paths import parse_object_key, repo_root


@dataclass(frozen=True)
class RetentionEntry:
    object_key: str
    suite_id: str
    version: str
    modified_at_utc: datetime


@dataclass(frozen=True)
class RetentionSummary:
    removed_local_files: int
    removed_cache_files: int
    removed_minio_objects: int


def apply_retention(
    env: RuntimeEnv,
    *,
    profile: str,
    suites: set[str] | None,
    ttl_candidates_days: int,
    keep_versions: int,
    dry_run: bool,
    with_minio: bool,
    minio_credentials: MinioCredentials | None,
) -> RetentionSummary:
    repo = repo_root()
    baseline_root = (repo / "qa" / "visual" / "baselines").resolve()
    cache_root = (repo / env.visual_cache_dir).resolve()
    cutoff_utc = datetime.now(UTC) - timedelta(days=ttl_candidates_days)

    local_entries = _scan_local_entries(baseline_root, profile=profile, suites=suites)
    to_remove = _select_keys_to_remove(
        local_entries,
        candidates_cutoff_utc=cutoff_utc,
        keep_versions=keep_versions,
    )

    removed_local = _remove_local_by_keys(
        baseline_root,
        to_remove,
        dry_run=dry_run,
        label="LOCAL",
    )
    removed_cache = _remove_local_by_keys(
        cache_root,
        to_remove,
        dry_run=dry_run,
        label="CACHE",
    )

    removed_minio = 0
    if with_minio:
        removed_minio = _remove_minio_by_policy(
            env,
            profile=profile,
            suites=suites,
            candidates_cutoff_utc=cutoff_utc,
            keep_versions=keep_versions,
            dry_run=dry_run,
            credentials=minio_credentials,
        )

    return RetentionSummary(
        removed_local_files=removed_local,
        removed_cache_files=removed_cache,
        removed_minio_objects=removed_minio,
    )


def _scan_local_entries(
    root: Path,
    *,
    profile: str,
    suites: set[str] | None,
) -> list[RetentionEntry]:
    out: list[RetentionEntry] = []
    if not root.is_dir():
        return out

    for path in sorted(root.rglob("*.png")):
        if not path.is_file():
            continue
        object_key = path.relative_to(root).as_posix()
        try:
            suite_id, parsed_profile, version, _rest = parse_object_key(object_key)
        except ValueError:
            continue
        if parsed_profile != profile:
            continue
        if suites and suite_id not in suites:
            continue
        try:
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        except OSError:
            continue
        out.append(
            RetentionEntry(
                object_key=object_key,
                suite_id=suite_id,
                version=version,
                modified_at_utc=modified,
            )
        )
    return out


def _select_keys_to_remove(
    entries: list[RetentionEntry],
    *,
    candidates_cutoff_utc: datetime,
    keep_versions: int,
) -> set[str]:
    remove_keys: set[str] = set()

    for entry in entries:
        if entry.version == "candidates" and entry.modified_at_utc < candidates_cutoff_utc:
            remove_keys.add(entry.object_key)

    versions_by_suite: dict[str, dict[str, datetime]] = {}
    for entry in entries:
        if entry.version in {"latest", "candidates"}:
            continue
        suite_map = versions_by_suite.setdefault(entry.suite_id, {})
        current = suite_map.get(entry.version)
        if current is None or entry.modified_at_utc > current:
            suite_map[entry.version] = entry.modified_at_utc

    for suite_id, suite_versions in versions_by_suite.items():
        ranked = sorted(suite_versions.items(), key=lambda item: (item[1], item[0]), reverse=True)
        keep_set = {name for name, _modified in ranked[:keep_versions]}
        for entry in entries:
            if entry.suite_id != suite_id:
                continue
            if entry.version in {"latest", "candidates"}:
                continue
            if entry.version not in keep_set:
                remove_keys.add(entry.object_key)

    return remove_keys


def _remove_local_by_keys(root: Path, object_keys: set[str], *, dry_run: bool, label: str) -> int:
    removed = 0
    for object_key in sorted(object_keys):
        path = root / object_key
        if not path.is_file():
            continue
        if dry_run:
            print(f"{label} RM {object_key}")
            removed += 1
            continue
        try:
            path.unlink(missing_ok=True)
            print(f"{label} RM {object_key}")
            removed += 1
        except Exception as exc:
            print(f"{label} FAIL {object_key}: {exc}")
    return removed


def _remove_minio_by_policy(
    env: RuntimeEnv,
    *,
    profile: str,
    suites: set[str] | None,
    candidates_cutoff_utc: datetime,
    keep_versions: int,
    dry_run: bool,
    credentials: MinioCredentials | None,
) -> int:
    ops = MinioOps(env, credentials=credentials)
    entries = _scan_minio_entries(ops, profile=profile, suites=suites)
    remove_keys = _select_keys_to_remove(
        entries,
        candidates_cutoff_utc=candidates_cutoff_utc,
        keep_versions=keep_versions,
    )

    removed = 0
    for object_key in sorted(remove_keys):
        if dry_run:
            print(f"MINIO RM {object_key}")
            removed += 1
            continue
        try:
            ops.remove_object(object_key)
            print(f"MINIO RM {object_key}")
            removed += 1
        except Exception as exc:
            print(f"MINIO FAIL {object_key}: {exc}")
    return removed


def _scan_minio_entries(ops: MinioOps, *, profile: str, suites: set[str] | None) -> list[RetentionEntry]:
    out: list[RetentionEntry] = []
    suite_prefixes = sorted(suites) if suites else [""]
    for suite_id in suite_prefixes:
        prefix = f"{suite_id}/{profile}/" if suite_id else ""
        for item in ops.list_objects(prefix):
            _append_minio_entry(out, item, profile=profile, suites=suites)
    return out


def _append_minio_entry(
    out: list[RetentionEntry],
    item: MinioObject,
    *,
    profile: str,
    suites: set[str] | None,
) -> None:
    try:
        suite_id, parsed_profile, version, _rest = parse_object_key(item.object_key)
    except ValueError:
        return
    if parsed_profile != profile:
        return
    if suites and suite_id not in suites:
        return
    out.append(
        RetentionEntry(
            object_key=item.object_key,
            suite_id=suite_id,
            version=version,
            modified_at_utc=item.last_modified_utc,
        )
    )
