from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.logger import configure_tools_logging
from tools.visual.baseline_ops.retention import apply_retention
from tools.visual.minio_credentials import resolve_runtime_minio_credentials


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Apply baseline retention policy for local storage and optional MinIO")
    parser.add_argument("--profile", default=None, help="Baseline profile (default: VISUAL_BASELINE_PROFILE)")
    parser.add_argument("--suite", action="append", default=[], help="Limit operation to selected suite")
    parser.add_argument("--ttl-candidates-days", type=int, default=7, help="Candidates retention TTL in days")
    parser.add_argument("--keep-versions", type=int, default=5, help="How many historical versions to keep per suite")
    parser.add_argument("--with-minio", action="store_true", help="Apply retention in MinIO bucket as well")
    parser.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --with-minio --apply)",
    )
    parser.add_argument("--minio-access-key", default="", help="MinIO access key used with --ask-release-credentials")
    parser.add_argument("--apply", action="store_true", help="Execute deletions. Default mode is dry-run")
    return parser


def main() -> int:
    log_path = configure_tools_logging("retention_baselines")
    logger.debug("tools_log_file", path=str(log_path), script="retention_baselines")

    args = _build_parser().parse_args()
    env = load_env()

    if args.ttl_candidates_days < 0:
        raise ValueError("--ttl-candidates-days must be >= 0")
    if args.keep_versions < 0:
        raise ValueError("--keep-versions must be >= 0")

    profile = str(args.profile or env.visual_baseline_profile).strip()
    suites = {str(item).strip() for item in args.suite if str(item).strip()} or None
    dry_run = not bool(args.apply)
    minio_credentials = resolve_runtime_minio_credentials(args, dry_run=dry_run, apply_flag="--apply")

    print("baseline retention")
    print(f"profile={profile}")
    print(f"suites={sorted(suites) if suites else 'ALL'}")
    print(f"ttl_candidates_days={args.ttl_candidates_days}")
    print(f"keep_versions={args.keep_versions}")
    print(f"with_minio={bool(args.with_minio)}")
    print(f"mode={'dry-run' if dry_run else 'apply'}")

    summary = apply_retention(
        env,
        profile=profile,
        suites=suites,
        ttl_candidates_days=int(args.ttl_candidates_days),
        keep_versions=int(args.keep_versions),
        dry_run=dry_run,
        with_minio=bool(args.with_minio),
        minio_credentials=minio_credentials,
    )

    print(
        "done: "
        f"removed_local_files={summary.removed_local_files}, "
        f"removed_cache_files={summary.removed_cache_files}, "
        f"removed_minio_objects={summary.removed_minio_objects}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
