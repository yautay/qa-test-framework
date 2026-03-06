from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileEntry:
    object_key: str
    absolute_path: Path
    size_bytes: int
    suite_id: str


@dataclass(frozen=True)
class CopyOp:
    action: str
    object_key: str
    source: Path | None
    target: Path
    size_bytes: int
    reason: str = ""


@dataclass(frozen=True)
class OperationSummary:
    copied: int
    skipped: int
    removed: int
    failed: int
    copied_bytes: int
    removed_bytes: int = 0
