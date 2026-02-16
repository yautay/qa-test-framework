from __future__ import annotations

"""Helper for preparing directories that collect test artifacts."""

from dataclasses import dataclass
from datetime import UTC, datetime
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


def build_run_artifacts(base_dir: str) -> RunArtifacts:
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

    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    root = Path(base_dir) / run_id
    traces = root / "traces"
    screenshots = root / "screenshots"
    videos = root / "videos"
    logs = root / "logs"
    for path in (root, traces, screenshots, videos, logs):
        path.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(run_id=run_id, root=root, traces=traces, screenshots=screenshots, videos=videos, logs=logs)
