from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from ..context import ReportServerContext

try:
    import reportlab.lib.pagesizes as _r_pagesizes
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    _REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _r_pagesizes = None
    ImageReader = None  # type: ignore[assignment]
    pdfmetrics = None  # type: ignore[assignment]
    TTFont = None  # type: ignore[assignment]
    canvas = None  # type: ignore[assignment]
    _REPORTLAB_AVAILABLE = False


_PDF_FONT_REGULAR = "Helvetica"
_PDF_FONT_BOLD = "Helvetica-Bold"


def _configure_pdf_fonts() -> tuple[str, str]:
    if not _REPORTLAB_AVAILABLE or pdfmetrics is None or TTFont is None:
        return _PDF_FONT_REGULAR, _PDF_FONT_BOLD

    regular_name = "VRTDejaVuSans"
    bold_name = "VRTDejaVuSansBold"
    regular_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if not regular_path.is_file() or not bold_path.is_file():
        return _PDF_FONT_REGULAR, _PDF_FONT_BOLD

    try:
        registered = set(pdfmetrics.getRegisteredFontNames())
        if regular_name not in registered:
            pdfmetrics.registerFont(TTFont(regular_name, str(regular_path)))
        if bold_name not in registered:
            pdfmetrics.registerFont(TTFont(bold_name, str(bold_path)))
        return regular_name, bold_name
    except Exception:
        logger.opt(exception=True).warning("unable to register unicode pdf fonts")
        return _PDF_FONT_REGULAR, _PDF_FONT_BOLD


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _value_by_path(root: dict[str, Any], dotted_path: str) -> Any:
    current: Any = root
    for token in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(token)
    return current


def _resolve_report_image(report_dir: Path, raw_path: str) -> Path | None:
    src = str(raw_path or "").strip()
    if not src:
        return None
    candidate = Path(src)
    if not candidate.is_absolute():
        candidate = (report_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(report_dir)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _resolve_baseline_image(context: ReportServerContext, report_dir: Path, row: dict[str, Any]) -> Path | None:
    direct = _resolve_report_image(report_dir, str(row.get("baseline_path", "")))
    if direct is not None:
        return direct
    suite_id = str(row.get("suite_id", "") or "").strip()
    scenario_id = str(row.get("scenario_id", "") or "").strip()
    viewport = str(row.get("viewport", "") or "").strip()
    browser = str(row.get("browser", "") or "").strip()
    if not (suite_id and scenario_id and viewport and browser):
        return None
    candidate = context.baseline_store.resolve_baseline(suite_id, scenario_id, viewport, browser)
    if candidate is None or not candidate.is_file():
        return None
    return candidate


def _draw_image_on_page(pdf: Any, image_path: Path, x: float, y: float, w: float, h: float) -> bool:
    if not _REPORTLAB_AVAILABLE or ImageReader is None:
        return False
    try:
        reader = ImageReader(str(image_path))
        img_w, img_h = reader.getSize()
        if img_w <= 0 or img_h <= 0:
            return False
        scale = min(w / float(img_w), h / float(img_h))
        draw_w = float(img_w) * scale
        draw_h = float(img_h) * scale
        draw_x = x + (w - draw_w) / 2.0
        draw_y = y + (h - draw_h) / 2.0
        pdf.drawImage(reader, draw_x, draw_y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
        return True
    except Exception:
        logger.opt(exception=True).warning("unable to draw image on pdf", image=str(image_path))
        return False


def _default_pdf_config() -> dict[str, Any]:
    return {
        "fields": [
            {"label": "run.tester", "path": "run.tester", "required": True},
            {"label": "run.run_note", "path": "run.run_note", "required": True},
            {"label": "scenario.name", "path": "scenario.name", "required": True},
            {"label": "scenario.suite_id", "path": "scenario.suite_id", "required": True},
            {"label": "scenario.target_url", "path": "scenario.target_url", "required": True},
            {"label": "scenario.viewport", "path": "scenario.viewport", "required": True},
            {"label": "scenario.browser", "path": "scenario.browser", "required": True},
            {"label": "scenario.capture.selector", "path": "scenario.capture.selector", "required": False},
            {"label": "Notatka BUG", "path": "bug.note", "required": False},
            {"label": "Notatka ASO", "path": "aso.note", "required": False},
        ],
        "images": [
            {"label": "baseline", "path": "image.baseline"},
            {"label": "actual", "path": "image.actual"},
            {"label": "diff", "path": "image.diff"},
            {"label": "heatmap", "path": "image.heatmap"},
        ],
    }


def _load_bug_pdf_config(config_path: Path | None) -> dict[str, Any]:
    cfg = _default_pdf_config()
    if config_path is None or not config_path.is_file():
        return cfg
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("bug pdf config invalid json", path=str(config_path))
        return cfg
    if not isinstance(data, dict):
        return cfg
    merged = dict(cfg)
    if isinstance(data.get("fields"), list):
        merged["fields"] = data["fields"]
    if isinstance(data.get("images"), list):
        merged["images"] = data["images"]
    return merged


def _generate_bug_pdf(
    *,
    context: ReportServerContext,
    run_id: str,
    report_dir: Path,
    bug_rows: list[tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[str, int]:
    if not bug_rows:
        return "", 0
    if not _REPORTLAB_AVAILABLE or canvas is None or _r_pagesizes is None:
        logger.warning("reportlab not available; BUG pdf was skipped", run_id=run_id)
        return "", 0

    config = _load_bug_pdf_config(context.bug_pdf_config_path)
    page_w, page_h = _r_pagesizes.landscape(_r_pagesizes.A4)
    output = report_dir / f"{run_id}.pdf"
    pdf = canvas.Canvas(str(output), pagesize=(page_w, page_h))
    font_regular, font_bold = _configure_pdf_fonts()

    raw_fields = config.get("fields")
    fields: list[Any] = raw_fields if isinstance(raw_fields, list) else []
    raw_images = config.get("images")
    image_defs: list[Any] = raw_images if isinstance(raw_images, list) else []

    for row, case_state in bug_rows:
        metadata = _as_dict(row.get("test_metadata"))
        run_meta = _as_dict(metadata.get("run"))
        scenario_meta = _as_dict(metadata.get("scenario"))
        bug_state = _as_dict(case_state.get("bug"))
        aso_state = _as_dict(case_state.get("aso"))
        source = {
            "run": {
                "run_id": run_id,
                "tester": str(run_meta.get("tester", row.get("tester", "")) or ""),
                "run_note": str(run_meta.get("run_note", row.get("run_note", "")) or ""),
            },
            "scenario": {
                "name": str(scenario_meta.get("name", row.get("scenario_id", "")) or ""),
                "suite_id": str(scenario_meta.get("suite_id", row.get("suite_id", "")) or ""),
                "target_url": str(scenario_meta.get("target_url", row.get("target_url", "")) or ""),
                "viewport": str(scenario_meta.get("viewport", row.get("viewport", "")) or ""),
                "browser": str(scenario_meta.get("browser", row.get("browser", "")) or ""),
                "capture": _as_dict(scenario_meta.get("capture")),
            },
            "bug": {
                "note": str(bug_state.get("note", "") or "").strip(),
            },
            "aso": {
                "note": str(aso_state.get("note", "") or "").strip(),
            },
        }

        pdf.setFont(font_bold, 14)
        pdf.drawString(24, page_h - 28, f"BUG report | run={run_id} | scenario={row.get('scenario_id', '')}")
        y = page_h - 52
        pdf.setFont(font_regular, 9)
        for field_def in fields:
            if not isinstance(field_def, dict):
                continue
            path = str(field_def.get("path", "") or "").strip()
            label = str(field_def.get("label", path) or path)
            required = bool(field_def.get("required", False))
            if not path:
                continue
            value = _value_by_path(source, path)
            text = str(value if value is not None else "").strip()
            if not text and not required:
                continue
            if not text and required:
                text = "(missing)"
            pdf.drawString(24, y, f"{label}: {text}")
            y -= 12
            if y < page_h * 0.55:
                break

        image_top = page_h * 0.52
        image_bottom = 30
        image_height = image_top - image_bottom
        col_gap = 12
        col_width = (page_w - 24 * 2 - col_gap) / 2.0
        row_height = (image_height - col_gap) / 2.0

        grid = [
            (24, image_bottom + row_height + col_gap),
            (24 + col_width + col_gap, image_bottom + row_height + col_gap),
            (24, image_bottom),
            (24 + col_width + col_gap, image_bottom),
        ]

        image_source = {
            "image": {
                "baseline": str(row.get("baseline_path", "") or ""),
                "actual": str(row.get("actual_path", "") or ""),
                "diff": str(row.get("diff_path", "") or ""),
                "heatmap": str(row.get("heatmap_path", "") or ""),
            }
        }
        baseline_resolved = _resolve_baseline_image(context, report_dir, row)

        for idx, image_def in enumerate(image_defs[:4]):
            if not isinstance(image_def, dict):
                continue
            label = str(image_def.get("label", "image") or "image")
            path = str(image_def.get("path", "") or "").strip()
            gx, gy = grid[idx]
            pdf.rect(gx, gy, col_width, row_height)
            pdf.setFont(font_bold, 8)
            pdf.drawString(gx + 4, gy + row_height - 11, label.upper())
            candidate: Path | None = None
            if path == "image.baseline" and baseline_resolved is not None:
                candidate = baseline_resolved
            elif path:
                raw = _value_by_path(image_source, path)
                candidate = _resolve_report_image(report_dir, str(raw or ""))
            if candidate is not None:
                _draw_image_on_page(pdf, candidate, gx + 4, gy + 4, col_width - 8, row_height - 18)
            else:
                pdf.setFont(font_regular, 8)
                pdf.drawString(gx + 6, gy + 8, "image unavailable")

        pdf.showPage()

    pdf.save()
    logger.info("bug_pdf_generated", run_id=run_id, pages=len(bug_rows), path=str(output))
    return str(output), len(bug_rows)
