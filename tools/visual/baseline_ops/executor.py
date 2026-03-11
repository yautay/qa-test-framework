from __future__ import annotations

import shutil
from pathlib import Path

from loguru import logger

from .types import CopyOp, OperationSummary


def plan_copy_ops(
    source_paths: dict[str, Path],
    target_paths: dict[str, Path],
    *,
    prune_missing: bool,
) -> list[CopyOp]:
    ops: list[CopyOp] = []

    for object_key, source in sorted(source_paths.items()):
        target = target_paths[object_key]
        size = _safe_size(source)
        if target.is_file() and _same_file_content(source, target):
            ops.append(CopyOp("skip", object_key, source, target, size, reason="unchanged"))
            continue
        ops.append(CopyOp("copy", object_key, source, target, size))

    if prune_missing:
        source_keys = set(source_paths.keys())
        for object_key, target in sorted(target_paths.items()):
            if object_key in source_keys:
                continue
            if target.is_file():
                ops.append(CopyOp("remove", object_key, None, target, _safe_size(target)))

    return ops


def execute_ops(ops: list[CopyOp], *, dry_run: bool) -> OperationSummary:
    copied = skipped = removed = failed = copied_bytes = removed_bytes = 0

    for op in ops:
        if op.action == "skip":
            skipped += 1
            logger.debug("baseline_copy_skip", object_key=op.object_key, reason=op.reason)
            continue

        if op.action == "copy":
            if dry_run:
                logger.debug("baseline_copy_dry_run", object_key=op.object_key)
                copied += 1
                copied_bytes += op.size_bytes
                continue
            try:
                op.target.parent.mkdir(parents=True, exist_ok=True)
                if op.source is None:
                    raise ValueError("copy op missing source path")
                shutil.copyfile(str(op.source), str(op.target))
                copied += 1
                copied_bytes += op.size_bytes
                logger.debug("baseline_copy_done", object_key=op.object_key)
            except Exception as exc:
                failed += 1
                logger.warning("baseline_copy_failed", object_key=op.object_key, error=str(exc))
            continue

        if op.action == "remove":
            if dry_run:
                logger.debug("baseline_remove_dry_run", object_key=op.object_key)
                removed += 1
                removed_bytes += op.size_bytes
                continue
            try:
                op.target.unlink(missing_ok=True)
                removed += 1
                removed_bytes += op.size_bytes
                logger.debug("baseline_remove_done", object_key=op.object_key)
            except Exception as exc:
                failed += 1
                logger.warning("baseline_remove_failed", object_key=op.object_key, error=str(exc))

    return OperationSummary(
        copied=copied,
        skipped=skipped,
        removed=removed,
        failed=failed,
        copied_bytes=copied_bytes,
        removed_bytes=removed_bytes,
    )


def print_summary(summary: OperationSummary, *, dry_run: bool) -> None:
    mode = "dry-run" if dry_run else "apply"
    copied_mib = summary.copied_bytes / (1024**2)
    removed_mib = summary.removed_bytes / (1024**2)
    print(
        f"done ({mode}): copied={summary.copied}, skipped={summary.skipped}, "
        f"removed={summary.removed}, failed={summary.failed}, "
        f"copied_size_mib={copied_mib:.2f}, removed_size_mib={removed_mib:.2f}"
    )


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _same_file_content(left: Path, right: Path) -> bool:
    try:
        left_stat = left.stat()
        right_stat = right.stat()
    except OSError:
        return False
    return left_stat.st_size == right_stat.st_size
