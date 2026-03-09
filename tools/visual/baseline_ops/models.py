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


@dataclass(frozen=True)
class VersionStats:
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class SyncTestsResult:
    local_orphans: list[str]
    cache_orphans: list[str]
    minio_orphans: list[str]
    parse_errors: list[str]
    local_removed: int
    cache_removed: int
    minio_removed: int
    local_failed: int
    cache_failed: int
    minio_failed: int

    @property
    def has_differences(self) -> bool:
        return bool(self.local_orphans or self.cache_orphans or self.minio_orphans or self.parse_errors)

    @property
    def has_failures(self) -> bool:
        return bool(self.local_failed or self.cache_failed or self.minio_failed or self.parse_errors)
