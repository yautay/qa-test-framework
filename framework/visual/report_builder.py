from __future__ import annotations

"""Emit JSON/HTML summaries for visual regression results."""

import json
from pathlib import Path

from framework.visual.models import VisualResult


def write_visual_report(report_dir: Path, results: list[VisualResult]) -> None:
    """Persist JSON + HTML artifacts that describe visual comparison outcomes."""

    report_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for result in results:
        rows.append(
            {
                "scenario_id": result.scenario_id,
                "status": result.status,
                "message": result.message,
                "compare_mode": result.compare_mode,
                "pixel_changed_ratio": result.pixel_changed_ratio,
                "lpips": result.lpips,
                "dists": result.dists,
                "baseline_path": result.baseline_path,
                "actual_path": result.actual_path,
                "diff_path": result.diff_path,
                "heatmap_path": result.heatmap_path,
                "thresholds": {
                    "pixel_max": result.thresholds.pixel_max,
                    "lpips_max": result.thresholds.lpips_max,
                    "dists_max": result.thresholds.dists_max,
                },
            }
        )

    (report_dir / "results.json").write_text(json.dumps({"results": rows}, indent=2), encoding="utf-8")

    lines = [
        "<html><head><meta charset='utf-8'><title>Visual Report</title></head><body>",
        "<h1>Visual Regression Report</h1>",
        "<table border='1' cellspacing='0' cellpadding='6'>",
        "<tr><th>Scenario</th><th>Status</th><th>Mode</th><th>Pixel</th><th>LPIPS</th><th>DISTS</th><th>Artifacts</th></tr>",
    ]

    for row in rows:
        artifacts = []
        for key in ("baseline_path", "actual_path", "diff_path", "heatmap_path"):
            value = row[key]
            if value:
                artifacts.append(f"{key}: {value}")
        artifacts_text = "<br/>".join(artifacts)
        lpips_text = "" if row["lpips"] is None else f"{float(row['lpips']):.6f}"
        dists_text = "" if row["dists"] is None else f"{float(row['dists']):.6f}"
        lines.append(
            "<tr>"
            f"<td>{row['scenario_id']}</td>"
            f"<td>{row['status']}</td>"
            f"<td>{row['compare_mode']}</td>"
            f"<td>{row['pixel_changed_ratio']:.6f}</td>"
            f"<td>{lpips_text}</td>"
            f"<td>{dists_text}</td>"
            f"<td>{artifacts_text}</td>"
            "</tr>"
        )
    lines.append("</table></body></html>")
    (report_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")
