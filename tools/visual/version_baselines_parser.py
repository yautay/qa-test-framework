from __future__ import annotations

from argparse import ArgumentParser


def build_parser() -> ArgumentParser:
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
    create.add_argument(
        "--source",
        choices=("auto", "baseline", "cache", "remote"),
        default="auto",
        help="Source store for --from-version (default: auto, baseline->cache fallback; remote=MinIO)",
    )
    create.add_argument("--prune-missing", action="store_true", help="Prune target files not present in source")
    create.add_argument("--with-minio", action="store_true", help="Also copy objects inside MinIO")
    create.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --with-minio --force)",
    )
    create.add_argument("--minio-access-key", default="", help="MinIO access key used with --ask-release-credentials")
    create.add_argument("--force", action="store_true", help="Execute writes. Default mode is dry-run")

    promote = sub.add_parser("promote", help="Promote a version into latest")
    promote.add_argument("--from-version", required=True, help="Source version")
    promote.add_argument(
        "--source",
        choices=("auto", "baseline", "cache", "remote"),
        default="auto",
        help="Source store for --from-version (default: auto, baseline->cache fallback; remote=MinIO)",
    )
    promote.add_argument("--prune-missing", action="store_true", help="Prune latest files not present in source")
    promote.add_argument("--with-minio", action="store_true", help="Also copy objects inside MinIO")
    promote.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --with-minio --force)",
    )
    promote.add_argument("--minio-access-key", default="", help="MinIO access key used with --ask-release-credentials")
    promote.add_argument("--force", action="store_true", help="Execute writes. Default mode is dry-run")

    recreate = sub.add_parser("recreate", help="Recreate local baselines from MinIO for selected tag")
    recreate.add_argument("--tag", dest="tag", default="latest", help="MinIO source tag/version (default: latest)")
    recreate.add_argument(
        "--from-version",
        dest="tag",
        help="Alias for --tag (kept for CLI consistency with create/promote)",
    )
    recreate.add_argument("--prune-missing", action="store_true", help="Prune local files not present in MinIO source")
    recreate.add_argument("--no-progress", action="store_true", help="Disable progress output during recreate")
    recreate.add_argument("--force", action="store_true", help="Execute writes. Default mode is dry-run")

    listed = sub.add_parser("list", help="List known baseline versions")
    listed.add_argument("--with-minio", action="store_true", help="Include MinIO versions")

    check = sub.add_parser("check", help="Compare local baselines with MinIO and report mismatches")
    check.add_argument("--tag", dest="tag", default="latest", help="Tag/version to compare (default: latest)")
    check.add_argument(
        "--from-version",
        dest="tag",
        help="Alias for --tag (kept for CLI consistency with create/promote)",
    )
    check.add_argument("--fast", action="store_true", help="Skip checksum and compare only presence + file size")
    check.add_argument("--no-progress", action="store_true", help="Disable progress output during check")
    check.add_argument("--limit", type=int, default=20, help="Maximum mismatch examples per category")
    check.add_argument(
        "--sync-tests",
        action="store_true",
        help="Validate/remove orphan baselines not linked to existing visual scenarios",
    )
    check.add_argument(
        "--with-minio",
        action="store_true",
        help="For --sync-tests: include MinIO objects in verification/cleanup",
    )
    check.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --sync-tests --with-minio --force)",
    )
    check.add_argument(
        "--minio-access-key",
        default="",
        help="MinIO access key used with --ask-release-credentials",
    )
    check.add_argument(
        "--force",
        action="store_true",
        help="For --sync-tests: execute deletions. Default mode is dry-run",
    )

    clean = sub.add_parser("clean", help="Clean local baselines/cache for selected tag or all tags")
    clean.add_argument("--tag", dest="tag", default="latest", help="Tag/version to clean (default: latest)")
    clean.add_argument(
        "--from-version",
        dest="tag",
        help="Alias for --tag (kept for CLI consistency with create/promote)",
    )
    clean.add_argument("--all", action="store_true", help="Clean all local tags/versions")
    clean.add_argument("--local", action="store_true", help="Clean only qa/visual/baselines")
    clean.add_argument("--cache", action="store_true", help="Clean only local cache mirror")
    clean.add_argument("--with-minio", action="store_true", help="Also clean objects inside MinIO")
    clean.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (for --with-minio --force)",
    )
    clean.add_argument("--minio-access-key", default="", help="MinIO access key used with --ask-release-credentials")
    clean.add_argument(
        "--allow-latest-minio-delete",
        action="store_true",
        help="Allow deleting latest tag in MinIO (safety override)",
    )
    clean.add_argument("--force", action="store_true", help="Execute deletions. Default mode is dry-run")

    return parser
