from __future__ import annotations

import shutil
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import settings
from framework.logger import configure_tools_logging

ARTIFACTS_DIR = REPO_ROOT / "artifacts"
TOOLS_LOGS_DIR = (REPO_ROOT / str(getattr(settings, "tools_logs_dir", "tools/logs") or "tools/logs")).resolve()
COMMON_CACHE_TARGETS = (
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
)
IGNORE_ROOTS_FOR_R_GLOB = {".git", ".venv", "venv", "node_modules", ".python313"}


@dataclass(frozen=True)
class CleanupResult:
    scanned: int
    removed: int
    removed_bytes: int


def _bytes_to_mib(size_bytes: int) -> float:
    return size_bytes / (1024**2)


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


def _remove_path(path: Path, dry_run: bool) -> int:
    size = _dir_size(path) if path.is_dir() else (path.stat().st_size if path.exists() and path.is_file() else 0)
    size_mib = _bytes_to_mib(size)
    print(f"remove: {path} ({size_mib:.2f} MiB)")
    if not dry_run:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
    return size


def _iter_tools_log_files() -> list[Path]:
    if not TOOLS_LOGS_DIR.is_dir():
        return []
    files: list[Path] = []
    for pattern in ("*.log", "*.log.*"):
        for path in TOOLS_LOGS_DIR.glob(pattern):
            if path.is_file():
                files.append(path)
    return sorted(set(files))


def _iter_common_cache_paths() -> list[Path]:
    paths = [(REPO_ROOT / item).resolve() for item in COMMON_CACHE_TARGETS]
    return [path for path in paths if path.exists()]


def _iter_pycache_dirs() -> list[Path]:
    pycache_dirs: list[Path] = []
    for path in REPO_ROOT.rglob("__pycache__"):
        if not path.is_dir():
            continue
        rel_parts = path.relative_to(REPO_ROOT).parts
        if any(part in IGNORE_ROOTS_FOR_R_GLOB for part in rel_parts):
            continue
        pycache_dirs.append(path)
    return sorted(set(pycache_dirs))


def cleanup_all(dry_run: bool) -> CleanupResult:
    run_dirs = _run_dirs()
    tools_log_files = _iter_tools_log_files()
    cache_paths = _iter_common_cache_paths()
    pycache_dirs = _iter_pycache_dirs()
    targets: list[Path] = [*run_dirs, *tools_log_files, *cache_paths, *pycache_dirs]

    removed = 0
    removed_bytes = 0

    for target in targets:
        size = _remove_path(target, dry_run=dry_run)
        removed_bytes += size
        removed += 1

    return CleanupResult(scanned=len(targets), removed=removed, removed_bytes=removed_bytes)


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
        size_mib = _bytes_to_mib(size)
        print(f"remove: {run_dir} ({size_mib:.2f} MiB)")
        if not dry_run:
            shutil.rmtree(run_dir, ignore_errors=True)

    return CleanupResult(scanned=len(dirs), removed=removed, removed_bytes=removed_bytes)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Clean local test artifacts, logs, and caches")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Remove run directories older than N days",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Remove run directories, tools logs, and common local caches",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting files",
    )
    return parser


def main() -> int:
    log_path = configure_tools_logging("artifacts_cleanup")
    logger.debug("tools_log_file", path=str(log_path), script="artifacts_cleanup")

    parser = _build_parser()
    args = parser.parse_args()

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
    size_mib = _bytes_to_mib(result.removed_bytes)
    print(f"cleanup complete ({mode}): scanned={result.scanned}, removed={result.removed}, removed: {size_mib:.2f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
