from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from loguru import logger

from framework.env import RuntimeEnv

from .executor import execute_ops, plan_copy_ops, print_summary
from .minio_ops import MinioCredentials, MinioObject, MinioOps
from .models import CheckResult, CleanResult, VersioningResult
from .paths import local_baseline_root, repo_root
from .scan_ops import scan_cache_version, scan_local_profile_files, scan_minio_version, to_file_entries
from .scanner import scan_local_version
from .types import FileEntry, OperationSummary


def recreate_from_minio(
    env: RuntimeEnv,
    *,
    profile: str,
    tag: str,
    suites: set[str] | None,
    dry_run: bool,
    prune_missing: bool,
    show_progress: bool = True,
) -> VersioningResult:
    repo = repo_root()
    baseline_root = local_baseline_root(repo)
    cache_root = (repo / env.visual_cache_dir).resolve()

    ops = MinioOps(env)
    print(f"scanning MinIO objects for profile={profile}, tag={tag}...")
    source_objects = scan_minio_version(ops, profile=profile, version=tag, suites=suites)
    if not source_objects:
        raise ValueError(f"no source PNG files found in MinIO for profile={profile!r}, tag={tag!r}")
    print(f"found {len(source_objects)} PNG files in MinIO")

    expected_keys = set(source_objects.keys())

    print("\n== Local baseline store ==")
    local_summary = _sync_minio_to_local_root(
        ops,
        source_objects=source_objects,
        target_root=baseline_root,
        dry_run=dry_run,
        progress_label="local",
        show_progress=show_progress,
    )
    if prune_missing:
        existing_local_target = scan_local_version(
            baseline_root,
            profile=profile,
            version=tag,
            suites=suites,
        )
        local_prune_summary = _prune_local_keys(
            {object_key: entry.absolute_path for object_key, entry in existing_local_target.items()},
            expected_keys=expected_keys,
            dry_run=dry_run,
        )
        local_summary = _combine_summaries(local_summary, local_prune_summary)
    print_summary(local_summary, dry_run=dry_run)

    print("\n== Local cache mirror ==")
    cache_summary = _sync_minio_to_local_root(
        ops,
        source_objects=source_objects,
        target_root=cache_root,
        dry_run=dry_run,
        progress_label="cache",
        show_progress=show_progress,
    )
    if prune_missing:
        existing_cache_target = scan_cache_version(cache_root, profile=profile, version=tag, suites=suites)
        cache_prune_summary = _prune_local_keys(
            existing_cache_target,
            expected_keys=expected_keys,
            dry_run=dry_run,
        )
        cache_summary = _combine_summaries(cache_summary, cache_prune_summary)
    print_summary(cache_summary, dry_run=dry_run)

    return VersioningResult(
        local_summary=local_summary,
        cache_summary=cache_summary,
        minio_copied=local_summary.copied,
        manifest_path=None,
    )


def clean_local_versions(
    env: RuntimeEnv,
    *,
    profile: str,
    tag: str,
    all_versions: bool,
    suites: set[str] | None,
    dry_run: bool,
    clean_local: bool,
    clean_cache: bool,
    with_minio: bool,
    minio_credentials: MinioCredentials | None,
    allow_latest_minio_delete: bool,
) -> CleanResult:
    repo = repo_root()
    baseline_root = local_baseline_root(repo)
    cache_root = (repo / env.visual_cache_dir).resolve()

    if not clean_local and not clean_cache:
        clean_local = True
        clean_cache = True

    local_summary = OperationSummary(copied=0, skipped=0, removed=0, failed=0, copied_bytes=0, removed_bytes=0)
    if clean_local:
        print("\n== Local baseline store ==")
        local_targets = scan_local_profile_files(
            baseline_root,
            profile=profile,
            version=None if all_versions else tag,
            suites=suites,
        )
        local_ops = plan_copy_ops({}, local_targets, prune_missing=True)
        local_summary = execute_ops(local_ops, dry_run=dry_run)
        print_summary(local_summary, dry_run=dry_run)

    cache_summary = OperationSummary(copied=0, skipped=0, removed=0, failed=0, copied_bytes=0, removed_bytes=0)
    if clean_cache:
        print("\n== Local cache mirror ==")
        cache_targets = scan_local_profile_files(
            cache_root,
            profile=profile,
            version=None if all_versions else tag,
            suites=suites,
        )
        cache_ops = plan_copy_ops({}, cache_targets, prune_missing=True)
        cache_summary = execute_ops(cache_ops, dry_run=dry_run)
        print_summary(cache_summary, dry_run=dry_run)

    minio_removed = 0
    minio_failed = 0
    if with_minio:
        if all_versions:
            raise ValueError("--with-minio --all is not allowed for safety")
        if tag == "latest" and not allow_latest_minio_delete:
            raise ValueError("deleting latest in MinIO requires --allow-latest-minio-delete")

        print("\n== MinIO ==")
        ops = MinioOps(env, credentials=minio_credentials)
        source_objects = scan_minio_version(ops, profile=profile, version=tag, suites=suites)
        for object_key in sorted(source_objects.keys()):
            if dry_run:
                logger.debug(f"MINIO RM {object_key}")
                minio_removed += 1
                continue
            try:
                ops.remove_object(object_key)
                logger.debug(f"MINIO RM {object_key}")
                minio_removed += 1
            except Exception as exc:
                minio_failed += 1
                logger.debug(f"MINIO FAIL {object_key}: {exc}")
        print(f"done ({'dry-run' if dry_run else 'apply'}): removed={minio_removed}, failed={minio_failed}")

    return CleanResult(
        local_summary=local_summary,
        cache_summary=cache_summary,
        minio_removed=minio_removed,
        minio_failed=minio_failed,
    )


def check_local_vs_minio(
    env: RuntimeEnv,
    *,
    profile: str,
    tag: str,
    suites: set[str] | None,
    fast: bool,
    show_progress: bool,
    limit: int,
    check_local: bool = True,
    check_cache: bool = True,
) -> CheckResult:
    repo = repo_root()
    baseline_root = local_baseline_root(repo)
    cache_root = (repo / env.visual_cache_dir).resolve()

    if not check_local and not check_cache:
        check_local = True
        check_cache = True

    ops = MinioOps(env)
    minio_entries = scan_minio_version(ops, profile=profile, version=tag, suites=suites)
    local_entries = (
        scan_local_version(
            baseline_root,
            profile=profile,
            version=tag,
            suites=suites,
        )
        if check_local
        else {}
    )
    cache_entries = (
        to_file_entries(
            scan_cache_version(
                cache_root,
                profile=profile,
                version=tag,
                suites=suites,
            )
        )
        if check_cache
        else {}
    )
    if not minio_entries and not local_entries and not cache_entries:
        raise ValueError(f"no PNG files found for profile={profile!r}, tag={tag!r} in local/cache/MinIO")

    mode = "fast(size+presence)" if fast else "checksum(sha256)"
    print("\n== Consistency check (vs MinIO) ==")
    print(f"profile={profile}")
    print(f"tag={tag}")
    print(f"suites={sorted(suites) if suites else 'ALL'}")
    print(f"mode={mode}")

    local_result = (
        _compare_entries_vs_minio(
            label="local",
            entries=local_entries,
            minio_entries=minio_entries,
            ops=ops,
            fast=fast,
            show_progress=show_progress,
            limit=limit,
        )
        if check_local
        else CheckResult(0, [], [], [], [], [])
    )
    cache_result = (
        _compare_entries_vs_minio(
            label="cache",
            entries=cache_entries,
            minio_entries=minio_entries,
            ops=ops,
            fast=fast,
            show_progress=show_progress,
            limit=limit,
        )
        if check_cache
        else CheckResult(0, [], [], [], [], [])
    )

    return CheckResult(
        matched=local_result.matched + cache_result.matched,
        missing_local=[f"local:{item}" for item in local_result.missing_local]
        + [f"cache:{item}" for item in cache_result.missing_local],
        missing_minio=[f"local:{item}" for item in local_result.missing_minio]
        + [f"cache:{item}" for item in cache_result.missing_minio],
        size_mismatch=[f"local:{item}" for item in local_result.size_mismatch]
        + [f"cache:{item}" for item in cache_result.size_mismatch],
        checksum_mismatch=[f"local:{item}" for item in local_result.checksum_mismatch]
        + [f"cache:{item}" for item in cache_result.checksum_mismatch],
        errors=[f"local:{item}" for item in local_result.errors] + [f"cache:{item}" for item in cache_result.errors],
    )


def _compare_entries_vs_minio(
    *,
    label: str,
    entries: dict[str, FileEntry],
    minio_entries: dict[str, MinioObject],
    ops: MinioOps,
    fast: bool,
    show_progress: bool,
    limit: int,
) -> CheckResult:
    entry_keys = set(entries.keys())
    minio_keys = set(minio_entries.keys())
    missing_local = sorted(minio_keys - entry_keys)
    missing_minio = sorted(entry_keys - minio_keys)

    common_keys = sorted(entry_keys & minio_keys)
    size_mismatch: list[str] = []
    checksum_mismatch: list[str] = []
    errors: list[str] = []
    matched = 0

    total = len(common_keys)
    is_tty = bool(show_progress and sys.stdout.isatty())
    next_percent_mark = 10
    for index, object_key in enumerate(common_keys, start=1):
        if show_progress:
            percent = int((index / total) * 100) if total else 100
            if is_tty:
                print(f"\rcheck:{label}: {index}/{total} ({percent:3d}%)", end="", flush=True)
            elif percent >= next_percent_mark or index == total:
                print(f"check:{label}: {index}/{total} ({percent}%)")
                while next_percent_mark <= percent:
                    next_percent_mark += 10

        local_entry = entries[object_key]
        minio_entry = minio_entries[object_key]
        if local_entry.size_bytes != minio_entry.size_bytes:
            size_mismatch.append(object_key)
            continue
        if fast:
            matched += 1
            continue
        try:
            local_hash = _sha256_file(local_entry.absolute_path)
            minio_hash = ops.object_sha256(object_key)
        except Exception as exc:
            errors.append(f"{object_key}: {exc}")
            continue
        if local_hash != minio_hash:
            checksum_mismatch.append(object_key)
            continue
        matched += 1

    if is_tty:
        print()

    result = CheckResult(
        matched=matched,
        missing_local=missing_local,
        missing_minio=missing_minio,
        size_mismatch=size_mismatch,
        checksum_mismatch=checksum_mismatch,
        errors=errors,
    )
    print(f"\n-- {label} vs MinIO --")
    print(
        "result: "
        f"matched={result.matched}, "
        f"missing_local={len(result.missing_local)}, "
        f"missing_minio={len(result.missing_minio)}, "
        f"size_mismatch={len(result.size_mismatch)}, "
        f"checksum_mismatch={len(result.checksum_mismatch)}, "
        f"errors={len(result.errors)}"
    )
    _print_examples("missing_local", result.missing_local, limit=limit)
    _print_examples("missing_minio", result.missing_minio, limit=limit)
    _print_examples("size_mismatch", result.size_mismatch, limit=limit)
    _print_examples("checksum_mismatch", result.checksum_mismatch, limit=limit)
    _print_examples("errors", result.errors, limit=limit)
    return result


def _sync_minio_to_local_root(
    ops: MinioOps,
    *,
    source_objects: dict[str, MinioObject],
    target_root: Path,
    dry_run: bool,
    progress_label: str,
    show_progress: bool,
) -> OperationSummary:
    copied = skipped = failed = copied_bytes = 0
    total = len(source_objects)
    is_tty = bool(show_progress and sys.stdout.isatty())
    next_percent_mark = 10

    for index, (object_key, source_object) in enumerate(sorted(source_objects.items()), start=1):
        if show_progress:
            percent = int((index / total) * 100) if total else 100
            if is_tty:
                print(f"\r{progress_label}: {index}/{total} ({percent:3d}%)", end="", flush=True)
            elif percent >= next_percent_mark or index == total:
                print(f"{progress_label}: {index}/{total} ({percent}%)")
                while next_percent_mark <= percent:
                    next_percent_mark += 10

        target_path = target_root / object_key
        target_size = _safe_size(target_path)
        if target_path.is_file() and target_size == source_object.size_bytes:
            logger.debug(f"SKIP  {object_key} (unchanged)")
            skipped += 1
            continue
        if dry_run:
            logger.debug(f"COPY  {object_key}")
            copied += 1
            copied_bytes += source_object.size_bytes
            continue
        try:
            ops.download_file(object_key, target_path)
            logger.debug(f"COPY  {object_key}")
            copied += 1
            copied_bytes += source_object.size_bytes
        except Exception as exc:
            failed += 1
            logger.debug(f"FAIL  {object_key}: {exc}")

    if is_tty:
        print()

    return OperationSummary(
        copied=copied,
        skipped=skipped,
        removed=0,
        failed=failed,
        copied_bytes=copied_bytes,
        removed_bytes=0,
    )


def _prune_local_keys(existing_paths: dict[str, Path], *, expected_keys: set[str], dry_run: bool) -> OperationSummary:
    removed = failed = removed_bytes = 0
    for object_key in sorted(set(existing_paths.keys()) - expected_keys):
        target = existing_paths[object_key]
        target_size = _safe_size(target)
        if dry_run:
            logger.debug(f"RM    {object_key}")
            removed += 1
            removed_bytes += target_size
            continue
        try:
            target.unlink(missing_ok=True)
            logger.debug(f"RM    {object_key}")
            removed += 1
            removed_bytes += target_size
        except Exception as exc:
            failed += 1
            logger.debug(f"FAIL  {object_key}: {exc}")
    return OperationSummary(
        copied=0,
        skipped=0,
        removed=removed,
        failed=failed,
        copied_bytes=0,
        removed_bytes=removed_bytes,
    )


def _combine_summaries(left: OperationSummary, right: OperationSummary) -> OperationSummary:
    return OperationSummary(
        copied=left.copied + right.copied,
        skipped=left.skipped + right.skipped,
        removed=left.removed + right.removed,
        failed=left.failed + right.failed,
        copied_bytes=left.copied_bytes + right.copied_bytes,
        removed_bytes=left.removed_bytes + right.removed_bytes,
    )


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 64)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _print_examples(label: str, items: list[str], *, limit: int) -> None:
    if not items:
        return
    shown = max(0, limit)
    print(f"{label} examples:")
    for item in items[:shown]:
        print(f"- {item}")
    remaining = len(items) - shown
    if remaining > 0:
        print(f"- ... and {remaining} more")
