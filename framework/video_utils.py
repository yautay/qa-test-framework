from __future__ import annotations

"""Helpers for trimming fail videos with ffmpeg and keeping retention size."""

import shutil
import subprocess
from pathlib import Path

from loguru import logger


def _safe_move(src: Path, dst: Path) -> None:
    """Move file safely across filesystems."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def ensure_min_fail_video(raw_video: Path, target_video: Path, min_seconds: int) -> Path:
    """Trim the raw sample to at least `min_seconds`, or keep the full capture if unavailable."""

    if not raw_video.is_file():
        logger.warning("video_trim_skipped_raw_missing", path=str(raw_video))
        return target_video

    if min_seconds <= 0:
        logger.warning("video_trim_skipped_invalid_min_seconds", min_seconds=int(min_seconds))
        _safe_move(raw_video, target_video)
        return target_video

    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin is None:
        logger.warning("video_trim_skipped_ffmpeg_missing")
        _safe_move(raw_video, target_video)
        return target_video

    target_video.parent.mkdir(parents=True, exist_ok=True)

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

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        logger.opt(exception=True).warning("video_trim_failed_ffmpeg_execution")
        _safe_move(raw_video, target_video)
        return target_video

    if result.returncode != 0:
        logger.warning(
            "video_trim_failed_non_zero_returncode",
            returncode=result.returncode,
            stderr=result.stderr[-500:] if result.stderr else "",
        )
        _safe_move(raw_video, target_video)
    else:
        raw_video.unlink(missing_ok=True)

    return target_video
