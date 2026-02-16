from __future__ import annotations

"""Emit JSON/HTML summaries for visual regression results (offline-friendly).

Outputs:
- results.json (machine-readable)
- index.html (offline, no fetch; embeds results inline)
- assets/ (bootstrap + vue + app.js)
"""

import json
import shutil
from pathlib import Path
from typing import Any

from framework.visual.models import VisualResult


def _as_str_path(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _maybe_relpath(path_str: str, report_dir: Path) -> str:
    """Return a relative posix path if path is within report_dir, else original string."""
    if not path_str:
        return ""
    try:
        p = Path(path_str)
        rel = p.relative_to(report_dir)
        return rel.as_posix()
    except Exception:
        return path_str


def _copy_report_assets(report_dir: Path) -> None:
    """Copy offline UI assets into report_dir/assets/."""
    assets_src = Path(__file__).resolve().parent / "report_assets"
    assets_dst = report_dir / "assets"
    assets_dst.mkdir(parents=True, exist_ok=True)

    required = (
        "bootstrap.min.css",
        "bootstrap.bundle.min.js",
        "vue.global.prod.js",
        "index.template.html",
        "app.module.js",
        "store.js",
        "viewer.js",
        "format.js",
    )

    for name in required:
        src = assets_src / name
        if not src.exists():
            raise FileNotFoundError(f"Missing report asset: {src}")
        shutil.copyfile(src, assets_dst / name)


def _build_rows(report_dir: Path, results: list[VisualResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        thresholds = getattr(result, "thresholds", None)

        baseline = _maybe_relpath(_as_str_path(result.baseline_path), report_dir)
        actual = _maybe_relpath(_as_str_path(result.actual_path), report_dir)
        diff = _maybe_relpath(_as_str_path(getattr(result, "diff_path", None)), report_dir)
        heatmap = _maybe_relpath(_as_str_path(getattr(result, "heatmap_path", None)), report_dir)

        rows.append(
            {
                "scenario_id": result.scenario_id,
                "status": result.status,
                "message": result.message,
                "compare_mode": result.compare_mode,
                "pixel_changed_ratio": result.pixel_changed_ratio,
                "lpips": result.lpips,
                "dists": result.dists,
                "baseline_path": baseline,
                "actual_path": actual,
                "diff_path": diff,
                "heatmap_path": heatmap,
                "thresholds": {
                    "pixel_max": getattr(thresholds, "pixel_max", None),
                    "lpips_max": getattr(thresholds, "lpips_max", None),
                    "dists_max": getattr(thresholds, "dists_max", None),
                },
            }
        )
    return rows


def _write_results_json(report_dir: Path, rows: list[dict[str, Any]]) -> None:
    (report_dir / "results.json").write_text(
        json.dumps({"results": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_offline_index_html(report_dir: Path, rows: list[dict[str, Any]]) -> None:
    """Generate index.html that works in file:// and http(s):// by embedding results inline."""
    template_path = report_dir / "assets" / "index.template.html"
    tpl = template_path.read_text(encoding="utf-8")

    # Safe JSON embedding: avoid "</script>" breaking out of script tag
    inline_json = json.dumps({"results": rows}, ensure_ascii=False).replace("</", "<\\/")

    html = tpl.replace("__VRT_INLINE_RESULTS__", inline_json)

    # Write main entry
    (report_dir / "index.html").write_text(html, encoding="utf-8")


def write_visual_report(report_dir: Path, results: list[VisualResult]) -> None:
    """Persist JSON + offline HTML report artifacts."""
    report_dir.mkdir(parents=True, exist_ok=True)

    # 1) Copy assets for offline usage
    _copy_report_assets(report_dir)

    # 2) Build rows with relative artifact paths (when possible)
    rows = _build_rows(report_dir, results)

    # 3) Machine-readable results
    _write_results_json(report_dir, rows)

    # 4) Offline-friendly index.template.html (no fetch)
    _write_offline_index_html(report_dir, rows)
