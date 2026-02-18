from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import token_urlsafe
from typing import Any
from urllib.parse import urlparse
import json
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.visual.baseline_store import BaselineStore


DEFAULT_PORT = 4173
CHALLENGE_TTL_SECONDS = 300


@dataclass
class ChallengeEntry:
    phrase: str
    expires_at: float


@dataclass
class ReportServerContext:
    report_dir: Path
    baseline_store: BaselineStore
    challenges: dict[str, ChallengeEntry] = field(default_factory=dict)


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


def _build_handler(context: ReportServerContext):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(context.report_dir), **kwargs)

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

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

        def do_PUT(self) -> None:
            path = urlparse(self.path).path
            if path != "/vrt-tags.json":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
                return

            try:
                payload = self._read_json_body()
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid request body: {exc}"})
                return

            target = context.report_dir / "vrt-tags.json"
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._send_json(HTTPStatus.OK, {"saved": True, "path": str(target)})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/baseline/challenge":
                _cleanup_expired_challenges(context)
                challenge_id = token_urlsafe(12)
                phrase = _generate_phrase()
                expires_at = time.time() + CHALLENGE_TTL_SECONDS
                context.challenges[challenge_id] = ChallengeEntry(phrase=phrase, expires_at=expires_at)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "challenge_id": challenge_id,
                        "phrase": phrase,
                        "expires_at": int(expires_at),
                    },
                )
                return

            if path != "/api/baseline/send":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": path})
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
                    source = _resolve_actual_png(context.report_dir, actual_path)
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
    parser = ArgumentParser(description="Serve visual report with baseline approval endpoints")
    parser.add_argument("--report-dir", default="", help="Path to visual report directory (artifacts/<run_id>/visual)")
    parser.add_argument("--run-id", default="", help="Run id under artifacts/<run_id>/visual")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    report_dir = _resolve_report_dir(REPO_ROOT, args.report_dir or None, args.run_id or None)
    env = load_env()
    context = ReportServerContext(
        report_dir=report_dir,
        baseline_store=BaselineStore(env, REPO_ROOT),
    )
    handler = _build_handler(context)
    server = ThreadingHTTPServer((args.host, int(args.port)), handler)

    print(f"visual report dir: {report_dir}")
    print(f"server listening: http://{args.host}:{args.port}/index.html")
    print("endpoints: PUT /vrt-tags.json, POST /api/baseline/challenge, POST /api/baseline/send")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down report server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
