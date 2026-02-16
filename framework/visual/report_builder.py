from __future__ import annotations

"""Emit JSON/HTML summaries for visual regression results."""

import json
from html import escape
from pathlib import Path

from framework.visual.models import VisualResult


def _fmt_float(value: float | None, digits: int = 6) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""


def _as_str_path(value) -> str:
    if value is None:
        return ""
    return str(value)


def _maybe_relpath(path_str: str, report_dir: Path) -> str:
    """Return a relative path (posix) if path is within report_dir, else original string."""
    if not path_str:
        return ""
    try:
        p = Path(path_str)
        rel = p.relative_to(report_dir)
        return rel.as_posix()
    except Exception:
        return path_str


def write_visual_report(report_dir: Path, results: list[VisualResult]) -> None:
    """Persist JSON + HTML artifacts that describe visual comparison outcomes."""

    report_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for result in results:
        thresholds = getattr(result, "thresholds", None)
        rows.append(
            {
                "scenario_id": result.scenario_id,
                "status": result.status,
                "message": result.message,
                "compare_mode": result.compare_mode,
                "pixel_changed_ratio": result.pixel_changed_ratio,
                "lpips": result.lpips,
                "dists": result.dists,
                "baseline_path": _as_str_path(result.baseline_path),
                "actual_path": _as_str_path(result.actual_path),
                "diff_path": _as_str_path(getattr(result, "diff_path", None)),
                "heatmap_path": _as_str_path(getattr(result, "heatmap_path", None)),
                "thresholds": {
                    "pixel_max": getattr(thresholds, "pixel_max", None),
                    "lpips_max": getattr(thresholds, "lpips_max", None),
                    "dists_max": getattr(thresholds, "dists_max", None),
                },
            }
        )

    (report_dir / "results.json").write_text(
        json.dumps({"results": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "<html><head><meta charset='utf-8'><title>Visual Report</title></head><body>",
        "<h1>Visual Regression Report</h1>",
        "<table border='1' cellspacing='0' cellpadding='6'>",
        "<tr><th>Scenario</th><th>Status</th><th>Mode</th><th>Pixel</th><th>LPIPS</th><th>DISTS</th><th>Message</th><th>Artifacts</th></tr>",
    ]

    for row in rows:
        artifacts = []
        for key in ("baseline_path", "actual_path", "diff_path", "heatmap_path"):
            value = row.get(key) or ""
            if not value:
                continue

            href = _maybe_relpath(value, report_dir)
            label = escape(key)

            # If it looks like a file path, make it clickable; otherwise show text
            if href and ("/" in href or "." in href):
                artifacts.append(f"{label}: <a href='{escape(href)}'>{escape(Path(href).name)}</a>")
            else:
                artifacts.append(f"{label}: {escape(value)}")

        artifacts_text = "<br/>".join(artifacts)

        lines.append(
            "<tr>"
            f"<td>{escape(str(row.get('scenario_id', '')))}</td>"
            f"<td>{escape(str(row.get('status', '')))}</td>"
            f"<td>{escape(str(row.get('compare_mode', '')))}</td>"
            f"<td>{escape(_fmt_float(row.get('pixel_changed_ratio')))}</td>"
            f"<td>{escape(_fmt_float(row.get('lpips'), digits=6))}</td>"
            f"<td>{escape(_fmt_float(row.get('dists'), digits=6))}</td>"
            f"<td>{escape(str(row.get('message', '') or ''))}</td>"
            f"<td>{artifacts_text}</td>"
            "</tr>"
        )

    lines.append("</table></body></html>")
    (report_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")
