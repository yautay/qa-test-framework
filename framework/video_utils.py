from __future__ import annotations

"""Helpers for trimming fail videos with ffmpeg and keeping retention size."""

import shutil
import subprocess
from pathlib import Path

from loguru import logger


def ensure_min_fail_video(raw_video: Path, target_video: Path, min_seconds: int) -> Path:
    """Trim the raw sample to at least `min_seconds`, or keep the full capture if unavailable."""

    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin is None:
        logger.warning("ffmpeg not found; preserving full video")
        raw_video.replace(target_video)
        return target_video

    command = [
        ffmpeg_bin,
        "-y",
        "-sseof",
        f"-{int(min_seconds)}",
        "-i",
        str(raw_video),
        "-c",
        "copy",
        str(target_video),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("ffmpeg trim failed; preserving full video")
        raw_video.replace(target_video)
    else:
        raw_video.unlink(missing_ok=True)
    return target_video
