from __future__ import annotations

import sys
from getpass import getpass
from argparse import ArgumentParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseline_ops import apply_version_copy, list_local_versions, list_minio_versions
from baseline_ops.minio_ops import MinioCredentials
from framework.env import load_env


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Version and promote visual baselines locally and optionally in MinIO")
    parser.add_argument(
        "--profile",
        default=None,
        help="Baseline profile (default: VISUAL_BASELINE_PROFILE)",
    )
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        help="Limit operation to selected suite (repeatable)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Copy baselines from one version into another")
    create.add_argument("--from-version", required=True, help="Source version")
    create.add_argument("--to-version", required=True, help="Target version")
    create.add_argument("--prune-missing", action="store_true", help="Prune target files not present in source")
    create.add_argument("--with-minio", action="store_true", help="Also copy objects inside MinIO")
    create.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --with-minio --apply)",
    )
    create.add_argument("--minio-access-key", default="", help="MinIO access key used with --ask-release-credentials")
    create.add_argument("--apply", action="store_true", help="Execute writes. Default mode is dry-run")

    promote = sub.add_parser("promote", help="Promote a version into latest")
    promote.add_argument("--from-version", required=True, help="Source version")
    promote.add_argument("--prune-missing", action="store_true", help="Prune latest files not present in source")
    promote.add_argument("--with-minio", action="store_true", help="Also copy objects inside MinIO")
    promote.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --with-minio --apply)",
    )
    promote.add_argument("--minio-access-key", default="", help="MinIO access key used with --ask-release-credentials")
    promote.add_argument("--apply", action="store_true", help="Execute writes. Default mode is dry-run")

    listed = sub.add_parser("list", help="List known baseline versions")
    listed.add_argument("--with-minio", action="store_true", help="Include MinIO versions")

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    env = load_env()

    profile = str(args.profile or env.visual_baseline_profile).strip()
    suites = {str(item).strip() for item in args.suite if str(item).strip()} or None

    try:
        if args.command == "list":
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

        if args.command == "create":
            dry_run = not bool(args.apply)
            minio_credentials = _resolve_runtime_minio_credentials(args, dry_run=dry_run)
            apply_version_copy(
                env,
                profile=profile,
                from_version=str(args.from_version).strip(),
                to_version=str(args.to_version).strip(),
                suites=suites,
                dry_run=dry_run,
                prune_missing=bool(args.prune_missing),
                with_minio=bool(args.with_minio),
                minio_credentials=minio_credentials,
                write_manifest_file=True,
            )
            return 0

        if args.command == "promote":
            dry_run = not bool(args.apply)
            minio_credentials = _resolve_runtime_minio_credentials(args, dry_run=dry_run)
            apply_version_copy(
                env,
                profile=profile,
                from_version=str(args.from_version).strip(),
                to_version="latest",
                suites=suites,
                dry_run=dry_run,
                prune_missing=bool(args.prune_missing),
                with_minio=bool(args.with_minio),
                minio_credentials=minio_credentials,
                write_manifest_file=True,
            )
            return 0
    except ValueError as exc:
        message = str(exc)
        print(f"error: {message}", file=sys.stderr)
        return 2 if "VISUAL_MINIO_ENDPOINT" in message else 1

    raise ValueError(f"unsupported command: {args.command}")


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
