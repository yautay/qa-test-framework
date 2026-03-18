from __future__ import annotations

"""Helper for preparing directories that collect test artifacts."""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RunArtifacts:
    """Paths for all artifact subdirectories belonging to a single run."""

    run_id: str
    root: Path
    traces: Path
    screenshots: Path
    videos: Path
    logs: Path


def resolve_artifacts_base_dir(base_dir: str, repo_root: Path) -> Path:
    """Resolve artifact base directory against repository root.

    Relative paths are anchored to repo_root to keep output stable even when
    pytest is started from a nested working directory.
    """

    token = (base_dir or "").strip() or "artifacts"
    candidate = Path(token)
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def build_run_artifacts(base_dir: str, run_id: str | None = None) -> RunArtifacts:
    """Ensure artifact directories exist and return their paths.

    Parameters
    ----------
    base_dir:
        Top-level directory under which a timestamped run folder is created.

    Returns
    -------
    RunArtifacts
        Object containing the paths to every artifact subdirectory.
    """

    resolved_run_id = str(run_id or os.getenv("PYTEST_XDIST_TESTRUNUID") or "").strip()
    if not resolved_run_id:
        resolved_run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    root = (Path(base_dir) / resolved_run_id).resolve()

    traces = root / "traces"
    screenshots = root / "screenshots"
    videos = root / "videos"
    logs = root / "logs"

    for path in (root, traces, screenshots, videos, logs):
        path.mkdir(parents=True, exist_ok=True)

    return RunArtifacts(
        run_id=resolved_run_id,
        root=root,
        traces=traces,
        screenshots=screenshots,
        videos=videos,
        logs=logs,
    )
