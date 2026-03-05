from __future__ import annotations

from pathlib import Path

from loguru import logger

from framework.env import RuntimeEnv

from .executor import execute_ops, plan_copy_ops, print_summary
from .manifest import write_manifest
from .minio_ops import MinioCredentials, MinioOps
from .models import VersioningResult
from .paths import local_baseline_root, repo_root, rewrite_object_key_version
from .scan_ops import scan_cache_version, scan_minio_version
from .scanner import scan_local_version
from .types import FileEntry


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
    dry_run: bool,
    prune_missing: bool,
    with_minio: bool,
    minio_credentials: MinioCredentials | None,
    write_manifest_file: bool,
) -> VersioningResult:
    repo = repo_root()
    baseline_root = local_baseline_root(repo)
    cache_root = (repo / env.visual_cache_dir).resolve()

    source_entries = scan_local_version(
        baseline_root,
        profile=profile,
        version=from_version,
        suites=suites,
    )
    if not source_entries:
        raise ValueError(f"no source PNG files found for profile={profile!r}, version={from_version!r}")

    local_source_paths: dict[str, Path] = {}
    local_target_paths: dict[str, Path] = {}
    cache_source_paths: dict[str, Path] = {}
    cache_target_paths: dict[str, Path] = {}

    for object_key, entry in source_entries.items():
        target_key = rewrite_object_key_version(object_key, to_version)
        local_source_paths[target_key] = entry.absolute_path
        local_target_paths[target_key] = baseline_root / target_key

        cache_source_paths[target_key] = cache_root / object_key
        cache_target_paths[target_key] = cache_root / target_key

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
            logger.debug(f"COPY  {source_key} -> {target_key}")
            copied += 1
            continue
        try:
            ops.copy_object(source_key, target_key)
            logger.debug(f"COPY  {source_key} -> {target_key}")
            copied += 1
        except Exception as exc:
            if _is_no_such_key_error(exc):
                try:
                    ops.upload_file(entry.absolute_path, target_key)
                    logger.debug(f"UPLOAD {entry.absolute_path} -> {target_key}")
                    copied += 1
                    uploaded += 1
                    continue
                except Exception as upload_exc:
                    failed += 1
                    logger.debug(f"FAIL  {source_key} -> {target_key}: {upload_exc}")
                    continue
            failed += 1
            logger.debug(f"FAIL  {source_key} -> {target_key}: {exc}")
    if prune_missing:
        target_prefixes = _minio_target_prefixes(profile=profile, version=to_version, suites=suites)
        existing_target_keys: set[str] = set()
        for prefix in target_prefixes:
            existing_target_keys.update(ops.list_keys(prefix))
        expected_target_keys = {rewrite_object_key_version(source_key, to_version) for source_key in source_entries}
        to_remove = sorted(existing_target_keys - expected_target_keys)
        for object_key in to_remove:
            if dry_run:
                logger.debug(f"RM    {object_key}")
                removed += 1
                continue
            try:
                ops.remove_object(object_key)
                logger.debug(f"RM    {object_key}")
                removed += 1
            except Exception as exc:
                failed += 1
                logger.debug(f"FAIL  {object_key}: {exc}")

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
