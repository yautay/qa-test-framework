from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import token_urlsafe
from threading import Lock
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
import json
import hashlib
import mimetypes
import re
import sys
import time

from loguru import logger

try:
    import reportlab.lib.pagesizes as _r_pagesizes
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    _REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _r_pagesizes = None
    ImageReader = None  # type: ignore[assignment]
    canvas = None  # type: ignore[assignment]
    _REPORTLAB_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.reporting_client import ReportingClient
from framework.visual.baseline_store import BaselineStore


DEFAULT_PORT = 4173
CHALLENGE_TTL_SECONDS = 300
_RUN_ID_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")
_READY_MARKER = ".report-ready.json"


@dataclass
class ChallengeEntry:
    run_id: str
    phrase: str
    expires_at: float


@dataclass
class ReportServerContext:
    repo_root: Path
    ui_dist_dir: Path
    baseline_store: BaselineStore
    run_dirs: dict[str, Path]
    pinned_run_dirs: dict[str, Path] = field(default_factory=dict)
    challenges: dict[str, ChallengeEntry] = field(default_factory=dict)
    reporting_client: ReportingClient | None = None
    reporting_bug_endpoint: str = ""
    reporting_aso_endpoint: str = ""
    reporting_note_endpoint: str = ""
    bug_pdf_config_path: Path | None = None
    _lock: Any = field(default_factory=Lock)

    def resolve_run_dir(self, run_id: str) -> Path | None:
        with self._lock:
            existing = self.run_dirs.get(run_id)
            if existing is not None:
                return existing
        self.refresh_run_dirs()
        with self._lock:
            return self.run_dirs.get(run_id)

    def refresh_run_dirs(self) -> None:
        discovered = _discover_visual_run_dirs(self.repo_root)
        for run_id, report_dir in self.pinned_run_dirs.items():
            if _is_ready_visual_dir(report_dir):
                discovered[run_id] = report_dir
        with self._lock:
            self.run_dirs = discovered

    def list_run_dirs(self) -> dict[str, Path]:
        self.refresh_run_dirs()
        with self._lock:
            return dict(self.run_dirs)


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


def _read_results_rows(report_dir: Path) -> list[dict[str, Any]]:
    results_path = report_dir / "results.json"
    if not results_path.is_file():
        return []
    try:
        data = json.loads(results_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = data.get("results") if isinstance(data, dict) else []
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)]


def _read_run_metadata(report_dir: Path) -> dict[str, str]:
    candidate = report_dir.parent / "run-metadata.json"
    if not candidate.is_file():
        return {"tester": "", "run_note": ""}
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return {"tester": "", "run_note": ""}
    if not isinstance(data, dict):
        return {"tester": "", "run_note": ""}
    return {
        "tester": str(data.get("tester", "") or "").strip(),
        "run_note": str(data.get("run_note", "") or "").strip(),
    }


def _report_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    failed = 0
    passed = 0
    uncertain = 0
    skipped = 0
    new_count = 0
    for row in rows:
        status = str(row.get("status", "")).strip().lower()
        if status == "failed":
            failed += 1
        elif status == "passed":
            passed += 1
        elif status == "uncertain":
            uncertain += 1
        elif status == "skipped":
            skipped += 1
        elif status == "new":
            new_count += 1
    return {
        "total": len(rows),
        "failed": failed,
        "passed": passed,
        "uncertain": uncertain,
        "skipped": skipped,
        "new": new_count,
    }


def _list_reports_payload(context: ReportServerContext) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    run_dirs = context.list_run_dirs()
    for run_id, report_dir in sorted(run_dirs.items(), key=lambda item: item[0], reverse=True):
        rows = _read_results_rows(report_dir)
        run_metadata = _read_run_metadata(report_dir)
        stats = _report_summary(rows)
        try:
            updated_at = int(report_dir.stat().st_mtime)
        except Exception:
            updated_at = 0
        reports.append(
            {
                "run_id": run_id,
                "report_dir": str(report_dir),
                "updated_at_epoch": updated_at,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(updated_at)) if updated_at else "",
                "total": stats["total"],
                "failed": stats["failed"],
                "passed": stats["passed"],
                "uncertain": stats["uncertain"],
                "skipped": stats["skipped"],
                "new": stats["new"],
                "tester": run_metadata.get("tester", ""),
                "run_note": run_metadata.get("run_note", ""),
            }
        )
    return reports


def _cleanup_expired_challenges(context: ReportServerContext) -> None:
    now = time.time()
    expired = [challenge_id for challenge_id, item in context.challenges.items() if item.expires_at <= now]
    for challenge_id in expired:
        context.challenges.pop(challenge_id, None)


def _generate_phrase() -> str:
    adjectives = ["amber", "calm", "delta", "frozen", "gentle", "rapid", "silent", "solar"]
    nouns = ["anchor", "bridge", "cloud", "forest", "harbor", "river", "signal", "valley"]
    idx = int(time.time() * 1000) % 100
    return f"{adjectives[idx % len(adjectives)]}-{nouns[(idx // 2) % len(nouns)]}-{idx:02d}"


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


def _as_non_empty_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid field: {key}")
    return value.strip()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")


def _content_type_for_path(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type:
        return mime_type
    return "application/octet-stream"


def _serve_file(handler: BaseHTTPRequestHandler, path: Path) -> None:
    if not path.is_file():
        handler.send_error(HTTPStatus.NOT_FOUND, "not found")
        return
    body = path.read_bytes()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", _content_type_for_path(path))
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _safe_run_id_or_error(raw_run_id: str) -> str:
    run_id = unquote(raw_run_id or "").strip()
    if not run_id or not _RUN_ID_SAFE.match(run_id):
        raise ValueError("invalid run_id")
    return run_id


def _tag_file_path(report_dir: Path) -> Path:
    return report_dir / "vrt-tags.json"


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
            {"label": "NOTATKA", "path": "note.text", "required": False},
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


def _normalize_single_tag_entry(raw: Any) -> dict[str, Any]:
    base = raw if isinstance(raw, dict) else {}
    note = base.get("note") if isinstance(base.get("note"), dict) else None
    note_text = ""
    if isinstance(note, dict):
        note_text = str(note.get("text", "") or "").strip()
    normalized_note = None
    if note_text:
        normalized_note = {
            "text": note_text,
            "updatedAt": str(note.get("updatedAt", "") or "") if isinstance(note, dict) else "",
        }
    return {
        "bug": bool(base.get("bug", False)),
        "aso": bool(base.get("aso", False)),
        "baseline": bool(base.get("baseline", False)),
        "note": normalized_note,
        "bug_reported": bool(base.get("bug_reported", False)),
        "aso_reported": bool(base.get("aso_reported", False)),
        "note_reported": bool(base.get("note_reported", False)),
        "bug_reported_at": str(base.get("bug_reported_at", "") or ""),
        "aso_reported_at": str(base.get("aso_reported_at", "") or ""),
        "note_reported_at": str(base.get("note_reported_at", "") or ""),
        "note_reported_hash": str(base.get("note_reported_hash", "") or ""),
    }


def _normalize_tag_snapshot(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        out[key] = _normalize_single_tag_entry(value)
    return out


def _read_tag_snapshot(report_dir: Path) -> dict[str, dict[str, Any]]:
    tag_file = _tag_file_path(report_dir)
    if not tag_file.is_file():
        return {}
    try:
        data = json.loads(tag_file.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return _normalize_tag_snapshot(data)


def _save_tag_snapshot(report_dir: Path, snapshot: dict[str, dict[str, Any]]) -> None:
    _tag_file_path(report_dir).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _row_tag_key(row: dict[str, Any]) -> str:
    return "::".join(
        [
            str(row.get("scenario_id", "") or ""),
            str(row.get("actual_path", "") or ""),
            str(row.get("baseline_path", "") or ""),
            str(row.get("diff_path", "") or ""),
        ]
    )


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


def _note_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_snapshot(snapshot: dict[str, Any]) -> str:
    try:
        encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except TypeError:
        encoded = json.dumps(snapshot, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_reporting_payload(
    run_id: str,
    tag: str,
    row: dict[str, Any],
    tag_entry: dict[str, Any],
    event_type: str = "visual_report",
) -> dict[str, Any]:
    metadata = _as_dict(row.get("test_metadata"))
    run_meta = _as_dict(metadata.get("run"))
    scenario_meta = _as_dict(metadata.get("scenario"))
    note_text = str(_as_dict(tag_entry.get("note")).get("text", "") or "").strip()
    return {
        "event_type": event_type,
        "run_id": run_id,
        "tag": tag,
        "scenario_id": str(row.get("scenario_id", "") or ""),
        "suite_id": str(row.get("suite_id", "") or scenario_meta.get("suite_id", "")),
        "viewport": str(row.get("viewport", "") or scenario_meta.get("viewport", "")),
        "browser": str(row.get("browser", "") or scenario_meta.get("browser", "")),
        "status": str(row.get("status", "") or ""),
        "message": str(row.get("message", "") or ""),
        "note": note_text,
        "metadata": metadata,
        "artifacts": {
            "baseline_path": str(row.get("baseline_path", "") or ""),
            "actual_path": str(row.get("actual_path", "") or ""),
            "diff_path": str(row.get("diff_path", "") or ""),
            "heatmap_path": str(row.get("heatmap_path", "") or ""),
        },
        "run": {
            "tester": str(run_meta.get("tester", row.get("tester", "")) or ""),
            "run_note": str(run_meta.get("run_note", row.get("run_note", "")) or ""),
        },
    }


def _read_last_audit_entry(report_dir: Path) -> dict[str, Any] | None:
    audit_path = report_dir / "reporting-audit.json"
    if not audit_path.is_file():
        return None
    try:
        loaded = json.loads(audit_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list) and len(loaded) > 0:
            last_item = loaded[-1]
            if isinstance(last_item, dict):
                return last_item
    except Exception:
        pass
    return None


def _had_previous_failures(audit_entry: dict[str, Any] | None) -> bool:
    if not audit_entry:
        return False
    prev_bug = audit_entry.get("bug", {})
    prev_aso = audit_entry.get("aso", {})
    prev_note = audit_entry.get("note", {})
    return prev_bug.get("failed", 0) > 0 or prev_aso.get("failed", 0) > 0 or prev_note.get("failed", 0) > 0


def _append_audit_entry(report_dir: Path, payload: dict[str, Any]) -> None:
    audit_path = report_dir / "reporting-audit.json"
    current: list[dict[str, Any]] = []
    if audit_path.is_file():
        try:
            loaded = json.loads(audit_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                current = [item for item in loaded if isinstance(item, dict)]
        except Exception:
            current = []
    current.append(payload)
    audit_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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

    raw_fields = config.get("fields")
    fields: list[Any] = raw_fields if isinstance(raw_fields, list) else []
    raw_images = config.get("images")
    image_defs: list[Any] = raw_images if isinstance(raw_images, list) else []

    for row, tag_entry in bug_rows:
        metadata = _as_dict(row.get("test_metadata"))
        run_meta = _as_dict(metadata.get("run"))
        scenario_meta = _as_dict(metadata.get("scenario"))
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
            "note": {
                "text": str(_as_dict(tag_entry.get("note")).get("text", "") or "").strip(),
            },
        }

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(24, page_h - 28, f"BUG report | run={run_id} | scenario={row.get('scenario_id', '')}")
        y = page_h - 52
        pdf.setFont("Helvetica", 9)
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
            pdf.setFont("Helvetica-Bold", 8)
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
                pdf.setFont("Helvetica", 8)
                pdf.drawString(gx + 6, gy + 8, "image unavailable")

        pdf.showPage()

    pdf.save()
    logger.info("bug_pdf_generated", run_id=run_id, pages=len(bug_rows), path=str(output))
    return str(output), len(bug_rows)


def _build_handler(context: ReportServerContext):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def handle(self):
            try:
                super().handle()
            except ConnectionAbortedError:
                pass

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            if content_length <= 0:
                return {}
            raw = self.rfile.read(content_length)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("request body must be a JSON object")
            return data

        def _serve_ui_index(self) -> None:
            _serve_file(self, context.ui_dist_dir / "index.html")

        def _serve_ui_asset(self, path: str) -> None:
            rel = path.lstrip("/")
            candidate = (context.ui_dist_dir / rel).resolve()
            try:
                candidate.relative_to(context.ui_dist_dir)
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN, "forbidden")
                return
            _serve_file(self, candidate)

        def _serve_report_file(self, run_id: str, rel_path: str) -> None:
            run_dir = context.resolve_run_dir(run_id)
            if run_dir is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                return

            clean_rel = rel_path.lstrip("/")
            candidate = (run_dir / clean_rel).resolve()
            try:
                candidate.relative_to(run_dir)
            except ValueError:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "path outside report directory"})
                return

            if not candidate.exists() and clean_rel.startswith("assets/"):
                self._serve_ui_asset(f"/{clean_rel}")
                return
            _serve_file(self, candidate)

        def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> bool:
            if path == "/api/reports":
                self._send_json(HTTPStatus.OK, {"reports": _list_reports_payload(context)})
                return True

            m_results = re.match(r"^/api/reports/([^/]+)/results$", path)
            if m_results:
                try:
                    run_id = _safe_run_id_or_error(m_results.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return True
                run_dir = context.resolve_run_dir(run_id)
                if run_dir is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return True
                rows = _read_results_rows(run_dir)
                run_metadata = _read_run_metadata(run_dir)
                tester = run_metadata.get("tester", "")
                run_note = run_metadata.get("run_note", "")
                enriched_rows: list[dict[str, Any]] = []
                for row in rows:
                    enriched = dict(row)
                    enriched.setdefault("tester", tester)
                    enriched.setdefault("run_note", run_note)
                    row_meta = enriched.get("test_metadata")
                    if not isinstance(row_meta, dict):
                        row_meta = {}
                    run_meta = row_meta.get("run")
                    if not isinstance(run_meta, dict):
                        run_meta = {}
                    run_meta.setdefault("run_id", run_id)
                    run_meta.setdefault("tester", tester)
                    run_meta.setdefault("run_note", run_note)
                    row_meta["run"] = run_meta
                    enriched["test_metadata"] = row_meta
                    enriched_rows.append(enriched)
                self._send_json(HTTPStatus.OK, {"run_id": run_id, "results": enriched_rows})
                return True

            m_ref = re.match(r"^/api/reports/([^/]+)/image/ref$", path)
            if m_ref:
                try:
                    run_id = _safe_run_id_or_error(m_ref.group(1))
                    if context.resolve_run_dir(run_id) is None:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                        return True

                    suite_id = (query.get("suite_id") or [""])[0].strip()
                    scenario_id = (query.get("scenario_id") or [""])[0].strip()
                    viewport = (query.get("viewport") or [""])[0].strip()
                    browser = (query.get("browser") or [""])[0].strip()
                    if not suite_id or not scenario_id or not viewport or not browser:
                        self._send_json(
                            HTTPStatus.BAD_REQUEST,
                            {"error": "missing required query params: suite_id, scenario_id, viewport, browser"},
                        )
                        return True

                    ref_path = context.baseline_store.resolve_baseline(suite_id, scenario_id, viewport, browser)
                    if ref_path is None or not ref_path.is_file():
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "baseline not found"})
                        return True
                    _serve_file(self, ref_path)
                    return True
                except Exception as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return True

            return False

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            m_tag = re.match(r"^/reports/([^/]+)/vrt-tags\.json$", path)
            if m_tag:
                try:
                    run_id = _safe_run_id_or_error(m_tag.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                run_dir = context.resolve_run_dir(run_id)
                if run_dir is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return
                tag_file = run_dir / "vrt-tags.json"
                if not tag_file.is_file():
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "tag file not found", "run_id": run_id})
                    return
                _serve_file(self, tag_file)
                return

            if path == "/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return

            if path.startswith("/api/"):
                handled = self._handle_api_get(path, query)
                if handled:
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
                return

            if path == "/" or path == "/index.html":
                self._serve_ui_index()
                return

            if path.startswith("/assets/"):
                self._serve_ui_asset(path)
                return

            m_report = re.match(r"^/reports/([^/]+)(?:/(.*))?$", path)
            if m_report:
                try:
                    run_id = _safe_run_id_or_error(m_report.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                rel_path = (m_report.group(2) or "").strip()
                if rel_path in {"", "index.html"}:
                    self._serve_ui_index()
                    return
                self._serve_report_file(run_id, rel_path)
                return

            self.send_error(HTTPStatus.NOT_FOUND, "not found")

        def do_PUT(self) -> None:
            path = urlparse(self.path).path
            m = re.match(r"^/reports/([^/]+)/vrt-tags\.json$", path)
            if not m:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
                return

            try:
                run_id = _safe_run_id_or_error(m.group(1))
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            run_dir = context.resolve_run_dir(run_id)
            if run_dir is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                return

            try:
                payload = self._read_json_body()
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid request body: {exc}"})
                return

            target = run_dir / "vrt-tags.json"
            normalized = _normalize_tag_snapshot(payload)
            target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._send_json(HTTPStatus.OK, {"saved": True, "path": str(target)})

        def do_POST(self) -> None:
            path = urlparse(self.path).path

            m_challenge = re.match(r"^/api/reports/([^/]+)/baseline/challenge$", path)
            if m_challenge:
                try:
                    run_id = _safe_run_id_or_error(m_challenge.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                if context.resolve_run_dir(run_id) is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return

                _cleanup_expired_challenges(context)
                challenge_id = token_urlsafe(12)
                phrase = _generate_phrase()
                expires_at = time.time() + CHALLENGE_TTL_SECONDS
                context.challenges[challenge_id] = ChallengeEntry(run_id=run_id, phrase=phrase, expires_at=expires_at)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "challenge_id": challenge_id,
                        "phrase": phrase,
                        "expires_at": int(expires_at),
                    },
                )
                return

            m_report_send = re.match(r"^/api/reports/([^/]+)/report/send$", path)
            if m_report_send:
                try:
                    run_id = _safe_run_id_or_error(m_report_send.group(1))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                report_dir = context.resolve_run_dir(run_id)
                if report_dir is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                    return

                payload = {}
                try:
                    payload = self._read_json_body()
                except Exception:
                    payload = {}

                incoming_tags = payload.get("tag_snapshot")
                if incoming_tags is not None:
                    normalized = _normalize_tag_snapshot(incoming_tags)
                    _save_tag_snapshot(report_dir, normalized)

                tag_snapshot = _read_tag_snapshot(report_dir)
                rows = _read_results_rows(report_dir)

                bug_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
                bug_sendable: list[tuple[dict[str, Any], dict[str, Any]]] = []
                aso_sendable: list[tuple[dict[str, Any], dict[str, Any]]] = []
                note_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
                note_sendable: list[tuple[dict[str, Any], dict[str, Any], str]] = []
                skipped_bug_locked = 0
                skipped_aso_locked = 0
                skipped_note_locked = 0

                for row in rows:
                    key = _row_tag_key(row)
                    tag_entry = tag_snapshot.get(key)
                    if tag_entry is None:
                        tag_entry = _normalize_single_tag_entry({})
                        tag_snapshot[key] = tag_entry
                    if tag_entry.get("bug"):
                        bug_rows.append((row, tag_entry))
                        if not bool(tag_entry.get("bug_reported", False)):
                            bug_sendable.append((row, tag_entry))
                        else:
                            skipped_bug_locked += 1
                    if tag_entry.get("aso"):
                        if not bool(tag_entry.get("aso_reported", False)):
                            aso_sendable.append((row, tag_entry))
                        else:
                            skipped_aso_locked += 1
                    note_text = str(_as_dict(tag_entry.get("note")).get("text", "") or "").strip()
                    if note_text:
                        note_rows.append((row, tag_entry))
                        current_hash = _note_hash(note_text)
                        previous_hash = str(tag_entry.get("note_reported_hash", "") or "").strip()
                        if not previous_hash or previous_hash != current_hash:
                            note_sendable.append((row, tag_entry, current_hash))
                        else:
                            skipped_note_locked += 1

                logger.info(
                    "report_send_start",
                    run_id=run_id,
                    bug_total=len(bug_rows),
                    bug_sendable=len(bug_sendable),
                    bug_skipped_locked=skipped_bug_locked,
                    aso_total=len(aso_sendable) + skipped_aso_locked,
                    aso_sendable=len(aso_sendable),
                    aso_skipped_locked=skipped_aso_locked,
                    note_total=len(note_rows),
                    note_sendable=len(note_sendable),
                    note_skipped_locked=skipped_note_locked,
                )
                logger.debug(
                    "report_send_debug",
                    run_id=run_id,
                    rows_count=len(rows),
                    tag_snapshot_count=len(tag_snapshot),
                    tag_snapshot_hash=_hash_snapshot(tag_snapshot),
                    has_client=context.reporting_client is not None,
                    bug_endpoint=str(context.reporting_bug_endpoint or "").strip(),
                    aso_endpoint=str(context.reporting_aso_endpoint or "").strip(),
                    note_endpoint=str(context.reporting_note_endpoint or "").strip(),
                )

                bug_ok = 0
                bug_failed = 0
                aso_ok = 0
                aso_failed = 0
                note_ok = 0
                note_failed = 0
                sent_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                has_client = context.reporting_client is not None
                if not has_client:
                    logger.warning("reporting client unavailable", run_id=run_id)

                for row, tag_entry, note_hash in note_sendable:
                    if not context.reporting_note_endpoint:
                        logger.warning("report_send_note_missing_endpoint", run_id=run_id)
                        note_failed += 1
                        continue

                    scenario_id = str(row.get("scenario_id", "") or "")
                    current_note_reported = bool(tag_entry.get("note_reported", False))
                    current_note_reported_at = str(tag_entry.get("note_reported_at", "") or "")
                    current_note_reported_hash = str(tag_entry.get("note_reported_hash", "") or "")

                    logger.debug(
                        "report_send_note_before_api",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        endpoint=context.reporting_note_endpoint,
                        note_reported=current_note_reported,
                        note_reported_at=current_note_reported_at,
                        note_reported_hash=current_note_reported_hash,
                        new_note_hash=note_hash,
                        hash_changed=current_note_reported_hash != note_hash,
                    )

                    req = _build_reporting_payload(
                        run_id,
                        "NOTE",
                        row,
                        tag_entry,
                        event_type="visual_report_note",
                    )
                    accepted = bool(
                        context.reporting_client
                        and context.reporting_client.send_payload(context.reporting_note_endpoint, req)
                    )

                    logger.debug(
                        "report_send_note_after_api",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        endpoint=context.reporting_note_endpoint,
                        accepted=accepted,
                        will_set_note_reported=accepted,
                        will_set_note_reported_at=accepted,
                        will_set_note_reported_hash=accepted,
                    )

                    if accepted:
                        old_note_reported = tag_entry.get("note_reported")
                        tag_entry["note_reported"] = True
                        tag_entry["note_reported_at"] = sent_at
                        tag_entry["note_reported_hash"] = note_hash
                        logger.debug(
                            "report_send_note_state_changed",
                            run_id=run_id,
                            scenario_id=scenario_id,
                            action="set_reported",
                            old_note_reported=old_note_reported,
                            new_note_reported=True,
                            new_note_reported_at=sent_at,
                            new_note_reported_hash=note_hash,
                        )
                        logger.info(
                            "report_send_note_success",
                            run_id=run_id,
                            scenario_id=scenario_id,
                        )
                        note_ok += 1
                    else:
                        logger.debug(
                            "report_send_note_state_unchanged",
                            run_id=run_id,
                            scenario_id=scenario_id,
                            action="keep_unreported",
                            current_note_reported=tag_entry.get("note_reported"),
                            current_note_reported_at=tag_entry.get("note_reported_at"),
                            current_note_reported_hash=tag_entry.get("note_reported_hash"),
                        )
                        logger.warning(
                            "report_send_note_failed",
                            run_id=run_id,
                            scenario_id=scenario_id,
                        )
                        note_failed += 1

                for row, tag_entry in aso_sendable:
                    if not context.reporting_aso_endpoint:
                        logger.warning("report_send_aso_missing_endpoint", run_id=run_id)
                        aso_failed += 1
                        continue

                    scenario_id = str(row.get("scenario_id", "") or "")
                    current_aso_reported = bool(tag_entry.get("aso_reported", False))
                    current_aso_reported_at = str(tag_entry.get("aso_reported_at", "") or "")

                    logger.debug(
                        "report_send_aso_before_api",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        endpoint=context.reporting_aso_endpoint,
                        aso_reported=current_aso_reported,
                        aso_reported_at=current_aso_reported_at,
                    )

                    req = _build_reporting_payload(run_id, "ASO", row, tag_entry)
                    accepted = bool(
                        context.reporting_client
                        and context.reporting_client.send_payload(context.reporting_aso_endpoint, req)
                    )

                    logger.debug(
                        "report_send_aso_after_api",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        endpoint=context.reporting_aso_endpoint,
                        accepted=accepted,
                        will_set_aso_reported=accepted,
                        will_set_aso_reported_at=accepted,
                    )

                    if accepted:
                        old_aso_reported = tag_entry.get("aso_reported")
                        tag_entry["aso_reported"] = True
                        tag_entry["aso_reported_at"] = sent_at
                        logger.debug(
                            "report_send_aso_state_changed",
                            run_id=run_id,
                            scenario_id=scenario_id,
                            action="set_reported",
                            old_aso_reported=old_aso_reported,
                            new_aso_reported=True,
                            new_aso_reported_at=sent_at,
                        )
                        logger.info(
                            "report_send_aso_success",
                            run_id=run_id,
                            scenario_id=scenario_id,
                        )
                        aso_ok += 1
                    else:
                        logger.debug(
                            "report_send_aso_state_unchanged",
                            run_id=run_id,
                            scenario_id=scenario_id,
                            action="keep_unreported",
                            current_aso_reported=tag_entry.get("aso_reported"),
                            current_aso_reported_at=tag_entry.get("aso_reported_at"),
                        )
                        logger.warning(
                            "report_send_aso_failed",
                            run_id=run_id,
                            scenario_id=scenario_id,
                        )
                        aso_failed += 1

                for row, tag_entry in bug_sendable:
                    if not context.reporting_bug_endpoint:
                        logger.warning("report_send_bug_missing_endpoint", run_id=run_id)
                        bug_failed += 1
                        continue

                    scenario_id = str(row.get("scenario_id", "") or "")
                    current_bug_reported = bool(tag_entry.get("bug_reported", False))
                    current_bug_reported_at = str(tag_entry.get("bug_reported_at", "") or "")

                    logger.debug(
                        "report_send_bug_before_api",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        endpoint=context.reporting_bug_endpoint,
                        bug_reported=current_bug_reported,
                        bug_reported_at=current_bug_reported_at,
                    )

                    req = _build_reporting_payload(run_id, "BUG", row, tag_entry)
                    accepted = bool(
                        context.reporting_client
                        and context.reporting_client.send_payload(context.reporting_bug_endpoint, req)
                    )

                    logger.debug(
                        "report_send_bug_after_api",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        endpoint=context.reporting_bug_endpoint,
                        accepted=accepted,
                        will_set_bug_reported=accepted,
                        will_set_bug_reported_at=accepted,
                    )

                    if accepted:
                        old_bug_reported = tag_entry.get("bug_reported")
                        tag_entry["bug_reported"] = True
                        tag_entry["bug_reported_at"] = sent_at
                        logger.debug(
                            "report_send_bug_state_changed",
                            run_id=run_id,
                            scenario_id=scenario_id,
                            action="set_reported",
                            old_bug_reported=old_bug_reported,
                            new_bug_reported=True,
                            new_bug_reported_at=sent_at,
                        )
                        logger.info(
                            "report_send_bug_success",
                            run_id=run_id,
                            scenario_id=scenario_id,
                        )
                        bug_ok += 1
                    else:
                        logger.debug(
                            "report_send_bug_state_unchanged",
                            run_id=run_id,
                            scenario_id=scenario_id,
                            action="keep_unreported",
                            current_bug_reported=tag_entry.get("bug_reported"),
                            current_bug_reported_at=tag_entry.get("bug_reported_at"),
                        )
                        logger.warning(
                            "report_send_bug_failed",
                            run_id=run_id,
                            scenario_id=scenario_id,
                        )
                        bug_failed += 1

                pdf_path, pdf_pages = _generate_bug_pdf(
                    context=context,
                    run_id=run_id,
                    report_dir=report_dir,
                    bug_rows=bug_rows,
                )

                previous_audit = _read_last_audit_entry(report_dir)
                had_previous_failures = _had_previous_failures(previous_audit)

                audit_entry = {
                    "timestamp_utc": sent_at,
                    "run_id": run_id,
                    "bug": {
                        "total": len(bug_rows),
                        "sent": bug_ok,
                        "failed": bug_failed,
                        "skipped_locked": skipped_bug_locked,
                    },
                    "aso": {
                        "sent": aso_ok,
                        "failed": aso_failed,
                        "skipped_locked": skipped_aso_locked,
                    },
                    "note": {
                        "total": len(note_rows),
                        "sent": note_ok,
                        "failed": note_failed,
                        "skipped_locked": skipped_note_locked,
                    },
                    "pdf": {
                        "path": pdf_path,
                        "pages": pdf_pages,
                    },
                }
                _save_tag_snapshot(report_dir, tag_snapshot)
                _append_audit_entry(report_dir, audit_entry)
                logger.info(
                    "report_send_finish",
                    run_id=run_id,
                    bug_sent=bug_ok,
                    bug_failed=bug_failed,
                    aso_sent=aso_ok,
                    aso_failed=aso_failed,
                    note_sent=note_ok,
                    note_failed=note_failed,
                    pdf_pages=pdf_pages,
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "accepted": True,
                        "run_id": run_id,
                        "previous_attempt_had_failures": had_previous_failures,
                        "bug": {
                            "total": len(bug_rows),
                            "sent": bug_ok,
                            "failed": bug_failed,
                            "skipped_locked": skipped_bug_locked,
                        },
                        "aso": {
                            "sent": aso_ok,
                            "failed": aso_failed,
                            "skipped_locked": skipped_aso_locked,
                        },
                        "note": {
                            "total": len(note_rows),
                            "sent": note_ok,
                            "failed": note_failed,
                            "skipped_locked": skipped_note_locked,
                        },
                        "pdf": {
                            "path": pdf_path,
                            "pages": pdf_pages,
                        },
                        "tag_snapshot": tag_snapshot,
                    },
                )
                return

            m_send = re.match(r"^/api/reports/([^/]+)/baseline/send$", path)
            if not m_send:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
                return

            try:
                run_id = _safe_run_id_or_error(m_send.group(1))
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            report_dir = context.resolve_run_dir(run_id)
            if report_dir is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "report not found", "run_id": run_id})
                return

            try:
                payload = self._read_json_body()
                challenge_id = _as_non_empty_text(payload, "challenge_id")
                phrase = _as_non_empty_text(payload, "phrase")
                items = payload.get("items")
                if not isinstance(items, list):
                    raise ValueError("missing or invalid field: items")
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return

            _cleanup_expired_challenges(context)
            challenge = context.challenges.get(challenge_id)
            if challenge is None:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "challenge is missing or expired"})
                return
            if challenge.phrase != phrase:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "challenge phrase mismatch"})
                return
            if challenge.run_id != run_id:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "challenge run mismatch"})
                return

            context.challenges.pop(challenge_id, None)

            results: list[dict[str, Any]] = []
            saved_count = 0
            failed_count = 0
            for raw_item in items:
                if not isinstance(raw_item, dict):
                    failed_count += 1
                    results.append({"status": "failed", "message": "item must be an object"})
                    continue
                try:
                    scenario_id = _as_non_empty_text(raw_item, "scenario_id")
                    suite_id = _as_non_empty_text(raw_item, "suite_id")
                    viewport = _as_non_empty_text(raw_item, "viewport")
                    browser = _as_non_empty_text(raw_item, "browser")
                    actual_path = _as_non_empty_text(raw_item, "actual_path")
                    source = _resolve_actual_png(report_dir, actual_path)
                    target = context.baseline_store.store_local_baseline(
                        suite_id,
                        scenario_id,
                        viewport,
                        browser,
                        source,
                    )
                    results.append(
                        {
                            "status": "saved",
                            "scenario_id": scenario_id,
                            "source_path": str(source),
                            "target_path": str(target),
                        }
                    )
                    saved_count += 1
                except Exception as exc:
                    failed_count += 1
                    results.append(
                        {
                            "status": "failed",
                            "scenario_id": str(raw_item.get("scenario_id", "")),
                            "message": str(exc),
                        }
                    )

            self._send_json(
                HTTPStatus.OK,
                {
                    "accepted": failed_count == 0,
                    "saved_count": saved_count,
                    "failed_count": failed_count,
                    "results": results,
                },
            )

    return Handler


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Serve visual reports with listing and baseline approval endpoints")
    parser.add_argument("--report-dir", default="", help="Path to visual report directory (artifacts/<run_id>/visual)")
    parser.add_argument("--run-id", default="", help="Run id under artifacts/<run_id>/visual")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    ui_dist_dir = (REPO_ROOT / "framework" / "visual" / "ui" / "dist").resolve()
    if not ui_dist_dir.is_dir():
        raise FileNotFoundError("UI build missing; run `npm run build` inside framework/visual/ui")

    run_dirs = _discover_visual_run_dirs(REPO_ROOT)
    selected_run_id = ""
    pinned_run_dirs: dict[str, Path] = {}
    if args.run_id or args.report_dir:
        selected_report_dir = _resolve_report_dir(REPO_ROOT, args.report_dir or None, args.run_id or None)
        selected_run_id = _run_id_from_visual_dir(REPO_ROOT, selected_report_dir)
        pinned_run_dirs[selected_run_id] = selected_report_dir

    env = load_env()
    reporting_client = ReportingClient(
        enabled=bool(str(env.reporting_api_url or "").strip()),
        base_url=env.reporting_api_url,
        token=env.reporting_api_token,
        timeout_seconds=env.reporting_api_timeout_seconds,
        retries=env.reporting_api_retries,
    )
    context = ReportServerContext(
        repo_root=REPO_ROOT,
        ui_dist_dir=ui_dist_dir,
        baseline_store=BaselineStore(env, REPO_ROOT),
        run_dirs=run_dirs,
        pinned_run_dirs=pinned_run_dirs,
        reporting_client=reporting_client,
        reporting_bug_endpoint=str(env.reporting_api_bug_endpoint or "").strip(),
        reporting_aso_endpoint=str(env.reporting_api_aso_endpoint or "").strip(),
        reporting_note_endpoint=str(env.reporting_api_note_endpoint or "").strip(),
        bug_pdf_config_path=(
            REPO_ROOT / "framework" / "visual" / "ui" / "src" / "config" / "bug_report_pdf_config.json"
        ),
    )
    handler = _build_handler(context)
    server = ThreadingHTTPServer((args.host, int(args.port)), handler)

    print(f"ui dist dir: {ui_dist_dir}")
    if selected_run_id:
        print(f"selected report: {selected_run_id} -> {pinned_run_dirs.get(selected_run_id)}")
        print(f"server listening: http://{args.host}:{args.port}/reports/{selected_run_id}")
    else:
        print(f"server listening: http://{args.host}:{args.port}/")
    print("endpoints: GET /api/reports, GET /api/reports/<run_id>/results, GET /api/reports/<run_id>/image/ref")
    print(
        "endpoints: PUT /reports/<run_id>/vrt-tags.json, "
        "POST /api/reports/<run_id>/baseline/challenge, "
        "POST /api/reports/<run_id>/baseline/send, "
        "POST /api/reports/<run_id>/report/send"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down report server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
