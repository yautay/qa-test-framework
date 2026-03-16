from __future__ import annotations

from pathlib import Path

from loguru import logger

from framework.env import RuntimeEnv

from .executor import execute_ops, plan_copy_ops, print_summary
from .manifest import write_manifest
from .minio_ops import MinioCredentials, MinioObject, MinioOps
from .models import VersioningResult
from .paths import local_baseline_root, repo_root, rewrite_object_key_version
from .scan_ops import scan_cache_version, scan_minio_version, to_file_entries
from .scanner import scan_local_version
from .types import FileEntry, OperationSummary


def promote_candidates_local(
    env: RuntimeEnv,
    *,
    profile: str,
    suites: set[str] | None,
    dry_run: bool,
    prune_missing: bool,
) -> VersioningResult:
    return apply_version_copy(
        env,
        profile=profile,
        from_version="candidates",
        to_version="latest",
        suites=suites,
        source="auto",
        dry_run=dry_run,
        prune_missing=prune_missing,
        with_minio=False,
        minio_credentials=None,
        write_manifest_file=False,
    )


def apply_version_copy(
    env: RuntimeEnv,
    *,
    profile: str,
    from_version: str,
    to_version: str,
    suites: set[str] | None,
    source: str = "auto",
    dry_run: bool,
    prune_missing: bool,
    with_minio: bool,
    minio_credentials: MinioCredentials | None,
    write_manifest_file: bool,
) -> VersioningResult:
    repo = repo_root()
    baseline_root = local_baseline_root(repo)
    cache_root = (repo / env.visual_cache_dir).resolve()
    source_normalized = str(source or "auto").strip().lower()
    if source_normalized not in {"auto", "baseline", "cache", "remote"}:
        raise ValueError("--source must be one of: auto, baseline, cache, remote")

    if source_normalized == "remote":
        print("source_store=remote")
        remote_ops = MinioOps(env, credentials=minio_credentials)
        source_objects = scan_minio_version(
            remote_ops,
            profile=profile,
            version=from_version,
            suites=suites,
        )
        if not source_objects:
            raise ValueError(f"no source PNG files found in MinIO for profile={profile!r}, version={from_version!r}")

        expected_target_keys = {rewrite_object_key_version(source_key, to_version) for source_key in source_objects}

        print("\n== Local baseline store ==")
        local_summary = _sync_minio_objects_to_root(
            remote_ops,
            source_objects=source_objects,
            to_version=to_version,
            target_root=baseline_root,
            dry_run=dry_run,
        )
        if prune_missing:
            existing_local_target = scan_local_version(
                baseline_root,
                profile=profile,
                version=to_version,
                suites=suites,
            )
            local_prune_summary = _prune_target_keys(
                {k: v.absolute_path for k, v in existing_local_target.items()},
                expected_target_keys=expected_target_keys,
                dry_run=dry_run,
            )
            local_summary = _combine_summaries(local_summary, local_prune_summary)
        print_summary(local_summary, dry_run=dry_run)

        print("\n== Local cache mirror ==")
        cache_summary = _sync_minio_objects_to_root(
            remote_ops,
            source_objects=source_objects,
            to_version=to_version,
            target_root=cache_root,
            dry_run=dry_run,
        )
        if prune_missing:
            existing_cache_target = scan_cache_version(cache_root, profile=profile, version=to_version, suites=suites)
            cache_prune_summary = _prune_target_keys(
                existing_cache_target,
                expected_target_keys=expected_target_keys,
                dry_run=dry_run,
            )
            cache_summary = _combine_summaries(cache_summary, cache_prune_summary)
        print_summary(cache_summary, dry_run=dry_run)

        minio_copied = 0
        if with_minio:
            minio_copied = _sync_minio_remote(
                remote_ops,
                source_keys=set(source_objects.keys()),
                to_version=to_version,
                dry_run=dry_run,
                prune_missing=prune_missing,
                profile=profile,
                suites=suites,
            )
    else:
        source_entries, source_store = _load_source_entries(
            baseline_root,
            cache_root,
            profile=profile,
            from_version=from_version,
            suites=suites,
            source=source_normalized,
        )
        source_cache_entries = scan_cache_version(cache_root, profile=profile, version=from_version, suites=suites)

        local_source_paths: dict[str, Path] = {}
        local_target_paths: dict[str, Path] = {}
        cache_source_paths: dict[str, Path] = {}
        cache_target_paths: dict[str, Path] = {}

        for object_key, entry in source_entries.items():
            target_key = rewrite_object_key_version(object_key, to_version)
            local_source_paths[target_key] = entry.absolute_path
            local_target_paths[target_key] = baseline_root / target_key

            cache_source_paths[target_key] = source_cache_entries.get(object_key, entry.absolute_path)
            cache_target_paths[target_key] = cache_root / target_key

        print(f"source_store={source_store}")

        existing_local_target = scan_local_version(
            baseline_root,
            profile=profile,
            version=to_version,
            suites=suites,
        )
        existing_cache_target = scan_cache_version(cache_root, profile=profile, version=to_version, suites=suites)

        local_ops = plan_copy_ops(
            local_source_paths,
            {
                **{k: v.absolute_path for k, v in existing_local_target.items()},
                **local_target_paths,
            },
            prune_missing=prune_missing,
        )
        cache_ops = plan_copy_ops(
            cache_source_paths,
            {
                **{k: v for k, v in existing_cache_target.items()},
                **cache_target_paths,
            },
            prune_missing=prune_missing,
        )

        print("\n== Local baseline store ==")
        local_summary = execute_ops(local_ops, dry_run=dry_run)
        print_summary(local_summary, dry_run=dry_run)

        print("\n== Local cache mirror ==")
        cache_summary = execute_ops(cache_ops, dry_run=dry_run)
        print_summary(cache_summary, dry_run=dry_run)

        minio_copied = 0
        if with_minio:
            minio_copied = _sync_minio(
                env,
                source_entries=source_entries,
                to_version=to_version,
                dry_run=dry_run,
                prune_missing=prune_missing,
                credentials=minio_credentials,
                profile=profile,
                suites=suites,
            )

    manifest_path: Path | None = None
    if write_manifest_file and not dry_run:
        final_entries = scan_local_version(
            baseline_root,
            profile=profile,
            version=to_version,
            suites=suites,
        )
        manifest_path = (baseline_root / "_manifests" / profile / f"{to_version}.json").resolve()
        write_manifest(
            manifest_path=manifest_path,
            profile=profile,
            version=to_version,
            source_version=from_version,
            files=final_entries,
        )
        print(f"manifest written: {manifest_path}")

    return VersioningResult(
        local_summary=local_summary,
        cache_summary=cache_summary,
        minio_copied=minio_copied,
        manifest_path=manifest_path,
    )


def _sync_minio_objects_to_root(
    ops: MinioOps,
    *,
    source_objects: dict[str, MinioObject],
    to_version: str,
    target_root: Path,
    dry_run: bool,
) -> OperationSummary:
    copied = skipped = failed = copied_bytes = 0
    for source_key, source_object in sorted(source_objects.items()):
        target_key = rewrite_object_key_version(source_key, to_version)
        target_path = target_root / target_key
        target_size = _safe_size(target_path)
        if target_path.is_file() and target_size == source_object.size_bytes:
            logger.debug("baseline_sync_skip_unchanged", target_key=target_key)
            skipped += 1
            continue
        if dry_run:
            logger.debug("baseline_sync_copy_dry_run", source_key=source_key, target_key=target_key)
            copied += 1
            copied_bytes += source_object.size_bytes
            continue
        try:
            ops.download_file(source_key, target_path)
            logger.debug("baseline_sync_copy_done", source_key=source_key, target_key=target_key)
            copied += 1
            copied_bytes += source_object.size_bytes
        except Exception as exc:
            failed += 1
            logger.warning("baseline_sync_copy_failed", source_key=source_key, target_key=target_key, error=str(exc))

    return OperationSummary(
        copied=copied,
        skipped=skipped,
        removed=0,
        failed=failed,
        copied_bytes=copied_bytes,
        removed_bytes=0,
    )


def _prune_target_keys(
    existing_paths: dict[str, Path],
    *,
    expected_target_keys: set[str],
    dry_run: bool,
) -> OperationSummary:
    to_remove = {
        object_key: target for object_key, target in existing_paths.items() if object_key not in expected_target_keys
    }
    if not to_remove:
        return OperationSummary(copied=0, skipped=0, removed=0, failed=0, copied_bytes=0, removed_bytes=0)
    remove_ops = plan_copy_ops({}, to_remove, prune_missing=True)
    return execute_ops(remove_ops, dry_run=dry_run)


def _combine_summaries(left: OperationSummary, right: OperationSummary) -> OperationSummary:
    return OperationSummary(
        copied=left.copied + right.copied,
        skipped=left.skipped + right.skipped,
        removed=left.removed + right.removed,
        failed=left.failed + right.failed,
        copied_bytes=left.copied_bytes + right.copied_bytes,
        removed_bytes=left.removed_bytes + right.removed_bytes,
    )


def _sync_minio_remote(
    ops: MinioOps,
    *,
    source_keys: set[str],
    to_version: str,
    dry_run: bool,
    prune_missing: bool,
    profile: str,
    suites: set[str] | None,
) -> int:
    copied = 0
    removed = 0
    failed = 0
    print("\n== MinIO copy ==")
    for source_key in sorted(source_keys):
        target_key = rewrite_object_key_version(source_key, to_version)
        if dry_run:
            logger.debug("baseline_minio_copy_dry_run", source_key=source_key, target_key=target_key)
            copied += 1
            continue
        try:
            ops.copy_object(source_key, target_key)
            logger.debug("baseline_minio_copy_done", source_key=source_key, target_key=target_key)
            copied += 1
        except Exception as exc:
            failed += 1
            logger.warning("baseline_minio_copy_failed", source_key=source_key, target_key=target_key, error=str(exc))
    if prune_missing:
        target_prefixes = _minio_target_prefixes(profile=profile, version=to_version, suites=suites)
        existing_target_keys: set[str] = set()
        for prefix in target_prefixes:
            existing_target_keys.update(ops.list_keys(prefix))
        expected_target_keys = {rewrite_object_key_version(source_key, to_version) for source_key in source_keys}
        to_remove = sorted(existing_target_keys - expected_target_keys)
        for object_key in to_remove:
            if dry_run:
                logger.debug("baseline_minio_remove_dry_run", object_key=object_key)
                removed += 1
                continue
            try:
                ops.remove_object(object_key)
                logger.debug("baseline_minio_remove_done", object_key=object_key)
                removed += 1
            except Exception as exc:
                failed += 1
                logger.warning("baseline_minio_remove_failed", object_key=object_key, error=str(exc))

    print(
        f"done ({'dry-run' if dry_run else 'apply'}): "
        f"minio_copied={copied}, minio_uploaded=0, minio_removed={removed}, minio_failed={failed}"
    )
    return copied


def _sync_minio(
    env: RuntimeEnv,
    *,
    source_entries: dict[str, FileEntry],
    to_version: str,
    dry_run: bool,
    prune_missing: bool,
    credentials: MinioCredentials | None,
    profile: str,
    suites: set[str] | None,
) -> int:
    ops = MinioOps(env, credentials=credentials)
    copied = 0
    uploaded = 0
    removed = 0
    failed = 0
    print("\n== MinIO copy ==")
    for source_key, entry in sorted(source_entries.items()):
        target_key = rewrite_object_key_version(source_key, to_version)
        if dry_run:
            logger.debug("baseline_minio_copy_dry_run", source_key=source_key, target_key=target_key)
            copied += 1
            continue
        try:
            ops.copy_object(source_key, target_key)
            logger.debug("baseline_minio_copy_done", source_key=source_key, target_key=target_key)
            copied += 1
        except Exception as exc:
            if _is_no_such_key_error(exc):
                try:
                    ops.upload_file(entry.absolute_path, target_key)
                    logger.debug(
                        "baseline_minio_upload_done",
                        source_path=str(entry.absolute_path),
                        target_key=target_key,
                    )
                    copied += 1
                    uploaded += 1
                    continue
                except Exception as upload_exc:
                    failed += 1
                    logger.warning(
                        "baseline_minio_upload_failed",
                        source_key=source_key,
                        target_key=target_key,
                        error=str(upload_exc),
                    )
                    continue
            failed += 1
            logger.warning(
                "baseline_minio_copy_failed",
                source_key=source_key,
                target_key=target_key,
                error=str(exc),
            )
    if prune_missing:
        target_prefixes = _minio_target_prefixes(profile=profile, version=to_version, suites=suites)
        existing_target_keys: set[str] = set()
        for prefix in target_prefixes:
            existing_target_keys.update(ops.list_keys(prefix))
        expected_target_keys = {rewrite_object_key_version(source_key, to_version) for source_key in source_entries}
        to_remove = sorted(existing_target_keys - expected_target_keys)
        for object_key in to_remove:
            if dry_run:
                logger.debug("baseline_minio_remove_dry_run", object_key=object_key)
                removed += 1
                continue
            try:
                ops.remove_object(object_key)
                logger.debug("baseline_minio_remove_done", object_key=object_key)
                removed += 1
            except Exception as exc:
                failed += 1
                logger.warning("baseline_minio_remove_failed", object_key=object_key, error=str(exc))

    print(
        f"done ({'dry-run' if dry_run else 'apply'}): "
        f"minio_copied={copied}, minio_uploaded={uploaded}, minio_removed={removed}, minio_failed={failed}"
    )
    return copied


def _minio_target_prefixes(*, profile: str, version: str, suites: set[str] | None) -> list[str]:
    if suites:
        return [f"{suite_id}/{profile}/{version}/" for suite_id in sorted(suites)]
    return [""]


def _is_no_such_key_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "nosuchkey" in text or "no such key" in text


def _load_source_entries(
    baseline_root: Path,
    cache_root: Path,
    *,
    profile: str,
    from_version: str,
    suites: set[str] | None,
    source: str,
) -> tuple[dict[str, FileEntry], str]:
    source_normalized = str(source or "auto").strip().lower()
    if source_normalized not in {"auto", "baseline", "cache"}:
        raise ValueError("--source must be one of: auto, baseline, cache")

    baseline_entries = scan_local_version(
        baseline_root,
        profile=profile,
        version=from_version,
        suites=suites,
    )
    cache_entries = to_file_entries(
        scan_cache_version(cache_root, profile=profile, version=from_version, suites=suites)
    )

    if source_normalized == "baseline":
        if baseline_entries:
            return baseline_entries, "baseline"
        raise ValueError(
            f"no source PNG files found in baseline store for profile={profile!r}, version={from_version!r}"
        )

    if source_normalized == "cache":
        if cache_entries:
            return cache_entries, "cache"
        raise ValueError(f"no source PNG files found in cache store for profile={profile!r}, version={from_version!r}")

    if baseline_entries:
        return baseline_entries, "baseline"
    if cache_entries:
        return cache_entries, "cache"
    raise ValueError(
        f"no source PNG files found for profile={profile!r}, version={from_version!r} in baseline or cache store"
    )


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
