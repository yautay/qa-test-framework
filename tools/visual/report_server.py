from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import token_urlsafe
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
import json
import mimetypes
import re
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.visual.baseline_store import BaselineStore


DEFAULT_PORT = 4173
CHALLENGE_TTL_SECONDS = 300
_RUN_ID_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


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
    challenges: dict[str, ChallengeEntry] = field(default_factory=dict)

    def resolve_run_dir(self, run_id: str) -> Path | None:
        return self.run_dirs.get(run_id)


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
        if visual_dir.is_dir():
            out[run_id] = visual_dir
    return out


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


def _report_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    failed = 0
    passed = 0
    new_count = 0
    for row in rows:
        status = str(row.get("status", "")).strip().lower()
        if status == "failed":
            failed += 1
        elif status == "passed":
            passed += 1
        elif status == "new":
            new_count += 1
    return {
        "total": len(rows),
        "failed": failed,
        "passed": passed,
        "new": new_count,
    }


def _list_reports_payload(context: ReportServerContext) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for run_id, report_dir in sorted(context.run_dirs.items(), key=lambda item: item[0], reverse=True):
        rows = _read_results_rows(report_dir)
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
                "new": stats["new"],
                "summary": f"failed={stats['failed']} passed={stats['passed']} new={stats['new']}",
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


def _build_handler(context: ReportServerContext):
    class Handler(BaseHTTPRequestHandler):
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
                self._send_json(HTTPStatus.OK, {"run_id": run_id, "results": _read_results_rows(run_dir)})
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
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    if args.run_id or args.report_dir:
        selected_report_dir = _resolve_report_dir(REPO_ROOT, args.report_dir or None, args.run_id or None)
        selected_run_id = _run_id_from_visual_dir(REPO_ROOT, selected_report_dir)
        run_dirs[selected_run_id] = selected_report_dir

    env = load_env()
    context = ReportServerContext(
        repo_root=REPO_ROOT,
        ui_dist_dir=ui_dist_dir,
        baseline_store=BaselineStore(env, REPO_ROOT),
        run_dirs=run_dirs,
    )
    handler = _build_handler(context)
    server = ThreadingHTTPServer((args.host, int(args.port)), handler)

    print(f"ui dist dir: {ui_dist_dir}")
    if selected_run_id:
        print(f"selected report: {selected_run_id} -> {run_dirs.get(selected_run_id)}")
        print(f"server listening: http://{args.host}:{args.port}/reports/{selected_run_id}")
    else:
        print(f"server listening: http://{args.host}:{args.port}/")
    print("endpoints: GET /api/reports, GET /api/reports/<run_id>/results, GET /api/reports/<run_id>/image/ref")
    print(
        "endpoints: PUT /reports/<run_id>/vrt-tags.json, POST /api/reports/<run_id>/baseline/challenge, POST /api/reports/<run_id>/baseline/send"
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
