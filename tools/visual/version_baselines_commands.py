from __future__ import annotations

from framework.env import RuntimeEnv
from tools.visual.baseline_ops import (
    apply_version_copy,
    check_local_vs_minio,
    clean_local_versions,
    local_version_stats,
    minio_version_stats,
    recreate_from_minio,
    sync_tests_with_baselines,
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
    print("local versions:")
    local_stats = local_version_stats(env, profile=profile, suites=suites)
    for version, stats in local_stats.items():
        print(f"- {version}: files={stats.file_count}, size={stats.total_bytes} ({_format_size(stats.total_bytes)})")
    local_total_files = sum(item.file_count for item in local_stats.values())
    local_total_bytes = sum(item.total_bytes for item in local_stats.values())
    print(f"TOTAL: files={local_total_files}, size={local_total_bytes} ({_format_size(local_total_bytes)})")

    if args.with_minio:
        print("minio versions:")
        minio_stats = minio_version_stats(env, profile=profile, suites=suites)
        for version, stats in minio_stats.items():
            print(
                f"- {version}: files={stats.file_count}, size={stats.total_bytes} ({_format_size(stats.total_bytes)})"
            )
        minio_total_files = sum(item.file_count for item in minio_stats.values())
        minio_total_bytes = sum(item.total_bytes for item in minio_stats.values())
        print(f"TOTAL: files={minio_total_files}, size={minio_total_bytes} ({_format_size(minio_total_bytes)})")
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
    if bool(getattr(args, "sync_tests", False)):
        dry_run = not bool(getattr(args, "force", False))
        minio_credentials = resolve_runtime_minio_credentials(args, dry_run=dry_run, apply_flag="--force")
        result = sync_tests_with_baselines(
            env,
            profile=profile,
            tag=str(args.tag).strip() or "latest",
            suites=suites,
            with_minio=bool(getattr(args, "with_minio", False)),
            dry_run=dry_run,
            limit=max(0, int(args.limit)),
            minio_credentials=minio_credentials,
        )
        if result.has_failures:
            return 1
        if dry_run and result.has_differences:
            return 1
        return 0

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


def _format_size(total_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(max(0, total_bytes))
    unit = units[0]
    for current in units:
        unit = current
        if value < 1024.0 or current == units[-1]:
            break
        value /= 1024.0
    return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} {unit}"
