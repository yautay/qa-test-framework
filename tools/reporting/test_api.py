from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import cgi
import json
import os


REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURE_FILE = REPO_ROOT / "tools" / "reporting" / "test_api_captures.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_dotenv() -> dict[str, str]:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _resolve_port() -> int:
    dotenv = _load_dotenv()
    value = os.getenv("TEST_API_PORT") or dotenv.get("TEST_API_PORT") or "58473"
    return int(value)


def _append_capture(record: dict) -> None:
    CAPTURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CAPTURE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _read_captures(limit: int = 200) -> list[dict]:
    if not CAPTURE_FILE.is_file():
        return []
    lines = CAPTURE_FILE.read_text(encoding="utf-8").splitlines()[-limit:]
    captures: list[dict] = []
    for line in lines:
        try:
            captures.append(json.loads(line))
        except Exception:
            continue
    return captures


def _latest_timing_logs(limit: int = 50) -> list[dict]:
    artifacts_root = REPO_ROOT / "artifacts"
    if not artifacts_root.is_dir():
        return []

    run_dirs = sorted([path for path in artifacts_root.iterdir() if path.is_dir()])
    if not run_dirs:
        return []

    latest_log = run_dirs[-1] / "logs" / "test_run.log"
    if not latest_log.is_file():
        return []

    rows: list[dict] = []
    for line in latest_log.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except Exception:
            continue
        record = payload.get("record", {})
        if record.get("message") not in {"test_case_timing", "context_timing"}:
            continue
        extra = record.get("extra", {})
        rows.append(
            {
                "message": record.get("message"),
                "time": record.get("time", {}).get("repr"),
                "nodeid": extra.get("nodeid"),
                "duration_seconds": extra.get("duration_seconds"),
                "status": extra.get("status"),
                "failed": extra.get("failed"),
                "scenario": extra.get("scenario"),
                "run_id": extra.get("run_id"),
                "git_user_name": extra.get("git_user_name"),
                "git_user_email": extra.get("git_user_email"),
            }
        )
    return rows[-limit:]


def _required_fields_for_event(event_type: str) -> list[str]:
    common = [
        "schema_version",
        "event_id",
        "event_type",
        "event_time_utc",
        "idempotency_key",
        "source",
    ]
    if event_type == "run_start":
        return common + ["run_id", "run_started_at", "execution", "target", "git"]
    if event_type == "test_result":
        return common + ["run_id", "test_id", "nodeid", "status", "attempt", "timing"]
    if event_type == "run_finish":
        return common + ["run_id", "run_finished_at", "exit_status", "duration_ms", "summary"]
    return common


def _v2_contract_issues(payload: dict | None) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload_not_json_object"]

    event_type = str(payload.get("event_type", "")).strip()
    if not event_type:
        return ["missing:event_type"]

    issues: list[str] = []
    for field in _required_fields_for_event(event_type):
        if field not in payload:
            issues.append(f"missing:{field}")
    if payload.get("schema_version") != "2.0":
        issues.append("schema_version_not_2.0")
    source = payload.get("source")
    if isinstance(source, dict):
        for key in ("project", "framework_version", "instance_id", "host", "user", "worker_id", "origin"):
            if key not in source:
                issues.append(f"missing:source.{key}")
    elif "source" in payload:
        issues.append("invalid:source_not_object")
    return issues


def _captures_summary(captures: list[dict]) -> dict:
    event_counts: dict[str, int] = {}
    schema_counts: dict[str, int] = {}
    idempotency_counts: dict[str, int] = {}
    issues: list[dict] = []

    for index, item in enumerate(captures):
        payload = item.get("payload")
        if not isinstance(payload, dict):
            continue

        event_type = str(payload.get("event_type", "unknown"))
        schema_version = str(payload.get("schema_version", "unknown"))
        idempotency_key = str(payload.get("idempotency_key", ""))

        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        schema_counts[schema_version] = schema_counts.get(schema_version, 0) + 1
        if idempotency_key:
            idempotency_counts[idempotency_key] = idempotency_counts.get(idempotency_key, 0) + 1

        item_issues = _v2_contract_issues(payload)
        if item_issues:
            issues.append(
                {
                    "index": index,
                    "path": item.get("path", ""),
                    "event_type": event_type,
                    "issues": item_issues,
                }
            )

    duplicate_idempotency = {key: count for key, count in idempotency_counts.items() if count > 1}
    return {
        "total_captures": len(captures),
        "event_counts": event_counts,
        "schema_counts": schema_counts,
        "duplicate_idempotency": duplicate_idempotency,
        "contract_issues": issues,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "tcms-test-api/1.0"

    def _send_json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "time": _utc_now()})
            return
        if self.path == "/captured":
            self._send_json(HTTPStatus.OK, {"captures": _read_captures()})
            return
        if self.path == "/captured/summary":
            captures = _read_captures(limit=2000)
            self._send_json(HTTPStatus.OK, _captures_summary(captures))
            return
        if self.path == "/logger/latest":
            self._send_json(HTTPStatus.OK, {"timings": _latest_timing_logs()})
            return
        if self.path == "/clear":
            CAPTURE_FILE.unlink(missing_ok=True)
            self._send_json(HTTPStatus.OK, {"status": "cleared"})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint", "path": self.path})

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        payload: dict | None = None
        files: list[dict] = []

        if content_type.startswith("application/json"):
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                payload = {"raw": raw_body.decode("utf-8", errors="replace")}
        elif content_type.startswith("multipart/form-data"):
            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(content_length),
            }
            form = cgi.FieldStorage(fp=BytesIO(raw_body), headers=self.headers, environ=environ)

            if "payload" in form:
                try:
                    payload = json.loads(form["payload"].value)
                except Exception:
                    payload = {"payload": form["payload"].value}

            if "screenshots" in form:
                field = form["screenshots"]
                fields = field if isinstance(field, list) else [field]
                for item in fields:
                    data = item.file.read() if item.file else b""
                    files.append(
                        {
                            "field": "screenshots",
                            "filename": item.filename,
                            "size_bytes": len(data),
                        }
                    )
        else:
            payload = {"raw": raw_body.decode("utf-8", errors="replace")}

        record = {
            "time": _utc_now(),
            "method": "POST",
            "path": self.path,
            "content_type": content_type,
            "payload": payload,
            "files": files,
            "headers": {
                "Authorization": self.headers.get("Authorization", ""),
                "User-Agent": self.headers.get("User-Agent", ""),
                "X-Idempotency-Key": self.headers.get("X-Idempotency-Key", ""),
            },
        }

        _append_capture(record)
        self._send_json(HTTPStatus.OK, {"status": "captured", "path": self.path})

    def log_message(self, format: str, *args) -> None:
        return


def main() -> int:
    port = _resolve_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Test API listening on http://127.0.0.1:{port}")
    print("GET /health         -> health check")
    print("GET /captured       -> captured API payloads")
    print("GET /captured/summary -> v2 contract summary and issues")
    print("GET /logger/latest  -> latest timing lines from Loguru")
    print("GET /clear          -> clear captures")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
