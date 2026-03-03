from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

_RUN_ID_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")
_READY_MARKER = ".report-ready.json"


def _latest_visual_report_dir(repo_root: Path) -> Path:
    artifacts_root = repo_root / "artifacts"
    if not artifacts_root.is_dir():
        raise FileNotFoundError("artifacts directory not found")

    candidates = sorted(
        [path / "visual" for path in artifacts_root.iterdir() if path.is_dir() and (path / "visual").is_dir()]
    )
    if not candidates:
        raise FileNotFoundError("no visual reports found under artifacts/<run_id>/visual")
    return candidates[-1]


def _resolve_report_dir(repo_root: Path, report_dir: str | None, run_id: str | None) -> Path:
    if run_id:
        candidate = (repo_root / "artifacts" / run_id / "visual").resolve()
        if not candidate.is_dir():
            raise FileNotFoundError(f"visual report directory not found for run_id={run_id!r}: {candidate}")
        return candidate

    if report_dir:
        candidate = Path(report_dir)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if not candidate.is_dir():
            raise FileNotFoundError(f"visual report directory not found: {candidate}")
        return candidate

    return _latest_visual_report_dir(repo_root)


def _run_id_from_visual_dir(repo_root: Path, report_dir: Path) -> str:
    try:
        rel = report_dir.resolve().relative_to((repo_root / "artifacts").resolve())
        parts = rel.parts
        if len(parts) >= 2 and parts[1] == "visual" and _RUN_ID_SAFE.match(parts[0]):
            return parts[0]
    except Exception:
        pass
    fallback = report_dir.parent.name.strip() or report_dir.name.strip() or "report"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", fallback)


def _discover_visual_run_dirs(repo_root: Path) -> dict[str, Path]:
    artifacts_root = repo_root / "artifacts"
    if not artifacts_root.is_dir():
        return {}
    out: dict[str, Path] = {}
    for run_dir in artifacts_root.iterdir():
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        if not _RUN_ID_SAFE.match(run_id):
            continue
        visual_dir = (run_dir / "visual").resolve()
        if _is_ready_visual_dir(visual_dir):
            out[run_id] = visual_dir
    return out


def _is_ready_visual_dir(visual_dir: Path) -> bool:
    if not visual_dir.is_dir():
        return False
    return (visual_dir / _READY_MARKER).is_file()


def _safe_run_id_or_error(raw_run_id: str) -> str:
    run_id = unquote(raw_run_id or "").strip()
    if not run_id or not _RUN_ID_SAFE.match(run_id):
        raise ValueError("invalid run_id")
    return run_id


def _resolve_actual_png(report_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (report_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(report_dir)
    except ValueError as exc:
        raise ValueError(f"actual_path outside report directory: {raw_path}") from exc

    if candidate.suffix.lower() != ".png":
        raise ValueError(f"actual_path must be a .png file: {raw_path}")
    if not candidate.is_file():
        raise ValueError(f"actual_path not found: {raw_path}")
    return candidate


def _build_dir(repo_root: Path, run_id: str) -> Path:
    artifacts_root = (repo_root / "artifacts").resolve()
    build_dir = (artifacts_root / run_id).resolve()
    try:
        build_dir.relative_to(artifacts_root)
    except ValueError as exc:
        raise ValueError("invalid build directory") from exc
    if not build_dir.is_dir():
        raise FileNotFoundError("build not found")
    return build_dir
