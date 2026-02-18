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
    """Copy the Vite build artifacts into report_dir/assets/."""
    build_root = Path(__file__).resolve().parent / "ui" / "dist"
    assets_src = build_root / "assets"
    if not assets_src.exists():
        raise FileNotFoundError("UI build missing; run `npm run build` inside framework/visual/ui")

    assets_dst = report_dir / "assets"
    if assets_dst.exists():
        shutil.rmtree(assets_dst)
    shutil.copytree(assets_src, assets_dst)


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
    """Generate index.html by embedding results into the Vite-built template."""
    build_index = Path(__file__).resolve().parent / "ui" / "dist" / "index.html"
    if not build_index.exists():
        raise FileNotFoundError("Vite build index.html missing; run `npm run build` inside framework/visual/ui")

    tpl = build_index.read_text(encoding="utf-8")
    if "__VRT_INLINE_RESULTS__" not in tpl:
        raise RuntimeError("Expected placeholder __VRT_INLINE_RESULTS__ in UI template")

    inline_json = json.dumps({"results": rows}, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("__VRT_INLINE_RESULTS__", inline_json)

    (report_dir / "index.html").write_text(html, encoding="utf-8")


def _ensure_tag_snapshot_file(report_dir: Path) -> None:
    tag_file = report_dir / "vrt-tags.json"
    if tag_file.exists():
        return
    tag_file.write_text("{}\n", encoding="utf-8")


def write_visual_report(report_dir: Path, results: list[VisualResult]) -> None:
    """Persist JSON + offline HTML report artifacts."""
    report_dir.mkdir(parents=True, exist_ok=True)
    _ensure_tag_snapshot_file(report_dir)

    # 1) Copy assets for offline usage
    _copy_report_assets(report_dir)

    # 2) Build rows with relative artifact paths (when possible)
    rows = _build_rows(report_dir, results)

    # 3) Machine-readable results
    _write_results_json(report_dir, rows)

    # 4) Offline-friendly index.template.html (no fetch)
    _write_offline_index_html(report_dir, rows)
