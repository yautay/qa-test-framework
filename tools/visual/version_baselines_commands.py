from __future__ import annotations

from framework.env import RuntimeEnv

from tools.visual.baseline_ops import (
    apply_version_copy,
    check_local_vs_minio,
    clean_local_versions,
    list_local_versions,
    list_minio_versions,
    recreate_from_minio,
)
from tools.visual.minio_credentials import resolve_runtime_minio_credentials


def run_command(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    if args.command == "list":
        return _handle_list(args, env, profile=profile, suites=suites)
    if args.command == "create":
        return _handle_create(args, env, profile=profile, suites=suites)
    if args.command == "promote":
        return _handle_promote(args, env, profile=profile, suites=suites)
    if args.command == "recreate":
        return _handle_recreate(args, env, profile=profile, suites=suites)
    if args.command == "clean":
        return _handle_clean(args, env, profile=profile, suites=suites)
    if args.command == "check":
        return _handle_check(args, env, profile=profile, suites=suites)
    raise ValueError(f"unsupported command: {args.command}")


def _handle_list(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    local_versions = list_local_versions(env, profile=profile, suites=suites)
    print("local versions:")
    for version in local_versions:
        print(f"- {version}")
    if args.with_minio:
        minio_versions = list_minio_versions(env, profile=profile, suites=suites)
        print("minio versions:")
        for version in minio_versions:
            print(f"- {version}")
    return 0


def _handle_create(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    dry_run = not bool(args.force)
    minio_credentials = resolve_runtime_minio_credentials(args, dry_run=dry_run, apply_flag="--force")
    apply_version_copy(
        env,
        profile=profile,
        from_version=str(args.from_version).strip(),
        to_version=str(args.to_version).strip(),
        suites=suites,
        source=str(getattr(args, "source", "auto") or "auto").strip().lower(),
        dry_run=dry_run,
        prune_missing=bool(args.prune_missing),
        with_minio=bool(args.with_minio),
        minio_credentials=minio_credentials,
        write_manifest_file=True,
    )
    return 0


def _handle_promote(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    dry_run = not bool(args.force)
    minio_credentials = resolve_runtime_minio_credentials(args, dry_run=dry_run, apply_flag="--force")
    apply_version_copy(
        env,
        profile=profile,
        from_version=str(args.from_version).strip(),
        to_version="latest",
        suites=suites,
        source=str(getattr(args, "source", "auto") or "auto").strip().lower(),
        dry_run=dry_run,
        prune_missing=bool(args.prune_missing),
        with_minio=bool(args.with_minio),
        minio_credentials=minio_credentials,
        write_manifest_file=True,
    )
    return 0


def _handle_recreate(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    dry_run = not bool(args.force)
    recreate_from_minio(
        env,
        profile=profile,
        tag=str(args.tag).strip() or "latest",
        suites=suites,
        dry_run=dry_run,
        prune_missing=bool(args.prune_missing),
        show_progress=not bool(args.no_progress),
    )
    return 0


def _handle_clean(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    dry_run = not bool(args.force)
    if bool(args.with_minio) and bool(args.all):
        raise ValueError("--with-minio --all is not allowed for safety")

    clean_tag = str(args.tag).strip() or "latest"
    if bool(args.with_minio) and clean_tag == "latest" and not bool(args.allow_latest_minio_delete):
        raise ValueError("deleting latest in MinIO requires --allow-latest-minio-delete")

    minio_credentials = resolve_runtime_minio_credentials(args, dry_run=dry_run, apply_flag="--force")
    clean_local = bool(args.local)
    clean_cache = bool(args.cache)
    if not clean_local and not clean_cache:
        clean_local = True
        clean_cache = True

    clean_local_versions(
        env,
        profile=profile,
        tag=clean_tag,
        all_versions=bool(args.all),
        suites=suites,
        dry_run=dry_run,
        clean_local=clean_local,
        clean_cache=clean_cache,
        with_minio=bool(args.with_minio),
        minio_credentials=minio_credentials,
        allow_latest_minio_delete=bool(args.allow_latest_minio_delete),
    )
    return 0


def _handle_check(args, env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> int:
    result = check_local_vs_minio(
        env,
        profile=profile,
        tag=str(args.tag).strip() or "latest",
        suites=suites,
        fast=bool(args.fast),
        show_progress=not bool(args.no_progress),
        limit=max(0, int(args.limit)),
        check_local=True,
        check_cache=True,
    )
    return 1 if result.has_differences else 0
