from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def local_baseline_root(repo: Path) -> Path:
    return (repo / "qa" / "visual" / "baselines").resolve()


def suite_version_dir(root: Path, suite_id: str, profile: str, version: str) -> Path:
    return (root / suite_id / profile / version).resolve()


def parse_object_key(object_key: str) -> tuple[str, str, str, str]:
    parts = object_key.split("/", 3)
    if len(parts) != 4:
        raise ValueError(f"invalid object key: {object_key!r}")
    return parts[0], parts[1], parts[2], parts[3]


def rewrite_object_key_version(object_key: str, to_version: str) -> str:
    suite_id, profile, _version, rest = parse_object_key(object_key)
    return f"{suite_id}/{profile}/{to_version}/{rest}"
