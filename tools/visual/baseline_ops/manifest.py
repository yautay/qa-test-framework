from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from .types import FileEntry


def write_manifest(
    *,
    manifest_path: Path,
    profile: str,
    version: str,
    source_version: str,
    files: dict[str, FileEntry],
) -> None:
    suites: dict[str, dict[str, int | str]] = defaultdict(lambda: {"file_count": 0, "suite_size_bytes": 0})
    total_size_bytes = 0

    file_rows: list[dict[str, str | int]] = []
    for object_key, entry in sorted(files.items()):
        total_size_bytes += entry.size_bytes
        suite_item = suites[entry.suite_id]
        suite_item["suite_id"] = entry.suite_id
        suite_item["file_count"] = int(suite_item["file_count"]) + 1
        suite_item["suite_size_bytes"] = int(suite_item["suite_size_bytes"]) + entry.size_bytes
        file_rows.append(
            {
                "object_key": object_key,
                "size_bytes": entry.size_bytes,
            }
        )

    suite_rows: list[dict[str, str | int | float]] = []
    for suite_id in sorted(suites.keys()):
        row = suites[suite_id]
        suite_bytes = int(row["suite_size_bytes"])
        suite_rows.append(
            {
                "suite_id": suite_id,
                "file_count": int(row["file_count"]),
                "suite_size_bytes": suite_bytes,
                "suite_size_mib": round(suite_bytes / (1024**2), 2),
            }
        )

    payload: dict[str, object] = {
        "profile": profile,
        "version": version,
        "source_version": source_version,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "file_count": len(files),
        "total_size_bytes": total_size_bytes,
        "total_size_mib": round(total_size_bytes / (1024**2), 2),
        "suites": suite_rows,
        "files": file_rows,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
