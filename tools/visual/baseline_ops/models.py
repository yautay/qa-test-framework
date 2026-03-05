from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .types import OperationSummary


@dataclass(frozen=True)
class VersioningResult:
    local_summary: OperationSummary
    cache_summary: OperationSummary
    minio_copied: int
    manifest_path: Path | None


@dataclass(frozen=True)
class CleanResult:
    local_summary: OperationSummary
    cache_summary: OperationSummary
    minio_removed: int
    minio_failed: int


@dataclass(frozen=True)
class CheckResult:
    matched: int
    missing_local: list[str]
    missing_minio: list[str]
    size_mismatch: list[str]
    checksum_mismatch: list[str]
    errors: list[str]

    @property
    def has_differences(self) -> bool:
        return bool(
            self.missing_local or self.missing_minio or self.size_mismatch or self.checksum_mismatch or self.errors
        )
