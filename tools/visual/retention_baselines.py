from __future__ import annotations

import sys
from argparse import ArgumentParser
from getpass import getpass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.visual.baseline_ops.minio_ops import MinioCredentials
from tools.visual.baseline_ops.retention import apply_retention
from framework.env import load_env


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
    args = _build_parser().parse_args()
    env = load_env()

    if args.ttl_candidates_days < 0:
        raise ValueError("--ttl-candidates-days must be >= 0")
    if args.keep_versions < 0:
        raise ValueError("--keep-versions must be >= 0")

    profile = str(args.profile or env.visual_baseline_profile).strip()
    suites = {str(item).strip() for item in args.suite if str(item).strip()} or None
    dry_run = not bool(args.apply)
    minio_credentials = _resolve_runtime_minio_credentials(args, dry_run=dry_run)

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


def _resolve_runtime_minio_credentials(args, *, dry_run: bool) -> MinioCredentials | None:
    with_minio = bool(getattr(args, "with_minio", False))
    ask = bool(getattr(args, "ask_release_credentials", False))
    if ask and not with_minio:
        raise ValueError("--ask-release-credentials requires --with-minio")
    if ask and dry_run:
        raise ValueError("--ask-release-credentials is allowed only with --apply")
    if not ask:
        return None

    access_key = str(getattr(args, "minio_access_key", "")).strip()
    if not access_key:
        access_key = input("MinIO release access key: ").strip()
    if not access_key:
        raise ValueError("missing MinIO release access key")
    secret_key = getpass("MinIO release secret key: ").strip()
    if not secret_key:
        raise ValueError("missing MinIO release secret key")
    return MinioCredentials(access_key=access_key, secret_key=secret_key)


if __name__ == "__main__":
    raise SystemExit(main())
