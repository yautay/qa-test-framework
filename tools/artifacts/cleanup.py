from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


@dataclass(frozen=True)
class CleanupResult:
    scanned: int
    removed: int
    removed_bytes: int


def _run_dirs() -> list[Path]:
    if not ARTIFACTS_DIR.is_dir():
        return []
    return sorted([path for path in ARTIFACTS_DIR.iterdir() if path.is_dir()])


def _dir_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total


def _is_older_than(path: Path, cutoff_utc: datetime) -> bool:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return False
    return mtime < cutoff_utc


def cleanup_all(dry_run: bool) -> CleanupResult:
    dirs = _run_dirs()
    removed = 0
    removed_bytes = 0

    for run_dir in dirs:
        size = _dir_size(run_dir)
        removed_bytes += size
        removed += 1
        print(f"remove: {run_dir} ({size} bytes)")
        if not dry_run:
            shutil.rmtree(run_dir, ignore_errors=True)

    return CleanupResult(scanned=len(dirs), removed=removed, removed_bytes=removed_bytes)


def cleanup_older(days: int, dry_run: bool) -> CleanupResult:
    dirs = _run_dirs()
    cutoff_utc = datetime.now(timezone.utc) - timedelta(days=days)
    removed = 0
    removed_bytes = 0

    for run_dir in dirs:
        if not _is_older_than(run_dir, cutoff_utc):
            continue
        size = _dir_size(run_dir)
        removed_bytes += size
        removed += 1
        print(f"remove: {run_dir} ({size} bytes)")
        if not dry_run:
            shutil.rmtree(run_dir, ignore_errors=True)

    return CleanupResult(scanned=len(dirs), removed=removed, removed_bytes=removed_bytes)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Clean test artifacts directory")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Remove run directories older than N days",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Remove all run directories under artifacts/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting files",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if not ARTIFACTS_DIR.exists():
        print(f"artifacts directory not found: {ARTIFACTS_DIR}")
        return 0

    if args.all and args.days is not None:
        parser.error("Use either --all or --days, not both")

    if not args.all and args.days is None:
        parser.error("Specify one mode: --all or --days N")

    if args.days is not None and args.days < 0:
        parser.error("--days must be >= 0")

    if args.all:
        result = cleanup_all(dry_run=args.dry_run)
    else:
        result = cleanup_older(days=int(args.days), dry_run=args.dry_run)

    mode = "dry-run" if args.dry_run else "delete"
    print(
        f"cleanup complete ({mode}): scanned={result.scanned}, "
        f"removed={result.removed}, removed_bytes={result.removed_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
