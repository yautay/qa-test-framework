from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "db_dump_config.json"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "out"


def find_chrome_executable() -> str:
    if sys.platform.startswith("linux"):
        candidates = [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
        ]
    elif sys.platform == "darwin":
        candidates = [shutil.which("google-chrome"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    elif sys.platform == "win32":
        candidates = [
            shutil.which("chrome"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ]
    else:
        candidates = []

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    raise FileNotFoundError("Chrome/Chromium executable not found")


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _to_int_or_default(value: str, default: int) -> int:
    token = _safe_str(value)
    if not token:
        return default
    try:
        return int(token)
    except ValueError:
        return default


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            "Config file not found: "
            f"{path}. Copy tools/dbeaver/db_dump_config.example.json to db_dump_config.json and fill your values."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config {path}: {exc}") from exc


def _wizard_settings(config: dict[str, Any]) -> tuple[str, str, bool, int]:
    wizard = config.get("wizard") if isinstance(config.get("wizard"), dict) else {}
    url = _safe_str((wizard or {}).get("url")) or "https://test-wizard.netcorner.pl/"
    auth_header = (
        _safe_str((wizard or {}).get("auth_header"))
        or _safe_str(os.getenv("WIZARD_AUTH_HEADER"))
        or _safe_str(os.getenv("WIZZARD_AUTH_HEADER"))
    )
    headless = bool((wizard or {}).get("headless", True))
    timeout_ms = _to_int_or_default(str((wizard or {}).get("timeout_ms", 30000)), 30000)
    if not auth_header:
        raise RuntimeError(
            "Missing wizard auth header. Fill wizard.auth_header in config or set WIZARD_AUTH_HEADER env variable."
        )
    return url, auth_header, headless, timeout_ms


def _parse_csv_tokens(raw_values: list[str]) -> list[str]:
    out: list[str] = []
    for raw in raw_values:
        for token in str(raw or "").split(","):
            normalized = _normalize(token)
            if normalized:
                out.append(normalized)
    return list(dict.fromkeys(out))


def _host_filter_tokens(config: dict[str, Any], args: argparse.Namespace) -> tuple[list[str], list[str]]:
    filters = config.get("filters") if isinstance(config.get("filters"), dict) else {}
    cfg_include = filters.get("include_host_tokens") if isinstance(filters.get("include_host_tokens"), list) else []
    cfg_exclude = filters.get("exclude_host_tokens") if isinstance(filters.get("exclude_host_tokens"), list) else []

    cli_include = _parse_csv_tokens(args.include_host or [])
    cli_exclude = _parse_csv_tokens(args.exclude_host or [])

    include_tokens = list(dict.fromkeys([_normalize(v) for v in cfg_include if _normalize(str(v))] + cli_include))
    exclude_tokens = list(dict.fromkeys([_normalize(v) for v in cfg_exclude if _normalize(str(v))] + cli_exclude))
    return include_tokens, exclude_tokens


def _host_allowed(host: str, include_tokens: list[str], exclude_tokens: list[str]) -> bool:
    normalized_host = _normalize(host)
    if include_tokens and not any(token in normalized_host for token in include_tokens):
        return False
    if exclude_tokens and any(token in normalized_host for token in exclude_tokens):
        return False
    return True


def _extract_records_from_dom(page: Page) -> list[dict[str, Any]]:
    payload = page.evaluate(
        r"""
() => {
  const clean = (v) => (v == null ? "" : String(v)).trim();
  const out = [];
  const controls = Array.from(
    document.querySelectorAll(
      "input[id*='-mysql-connection'], input[id*='-mariadb-connection']"
    )
  );

  for (const el of controls) {
    const id = clean(el.getAttribute("id"));
    const value = clean(el.value || el.getAttribute("value") || "");
    if (!id || !value) continue;

    const suffix = id.endsWith("-mysql-connection") ? "-mysql-connection" : "-mariadb-connection";
    const vmId = id.slice(0, id.length - suffix.length);
    const envHeading = el.closest("div[id^='collapse']")?.previousElementSibling?.querySelector("div[id^='heading']");
    const envName = clean(envHeading?.textContent || envHeading?.getAttribute("id") || "");

    out.push({
      vm_id: vmId,
      env: envName,
      row_id: id,
      fields: [
        {
          id,
          name: clean(el.getAttribute("name")),
          type: clean(el.getAttribute("type")).toLowerCase(),
          value,
          label: id,
        },
      ],
    });
  }

  return out;
}
        """
    )
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _open_wizard(url: str, auth_header: str, headless: bool, timeout_ms: int) -> tuple[Playwright, Browser, Page]:
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=headless,
        executable_path=find_chrome_executable(),
        args=["--no-sandbox", "--ignore-certificate-errors"],
    )
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.set_extra_http_headers({"Authorization": auth_header})
    page.on("dialog", lambda dialog: dialog.dismiss())
    page.goto(url, wait_until="networkidle", timeout=timeout_ms)
    return pw, browser, page


@dataclass
class DbEndpoint:
    engine: str
    host: str
    port: str
    database: str
    username: str
    password: str


def _extract_from_url(value: str) -> tuple[str, str, str]:
    token = _safe_str(value)
    if not token:
        return "", "", ""
    patterns = [
        r"(?:jdbc:)?(?:mysql|mariadb)://(?P<host>[^:/?#]+)(?::(?P<port>\d+))?(?:/(?P<db>[^?\s;]+))?",
        r"(?P<host>[a-zA-Z0-9_.-]+):(?P<port>\d{2,5})(?:/(?P<db>[a-zA-Z0-9_.-]+))?",
    ]
    for pattern in patterns:
        match = re.search(pattern, token, flags=re.IGNORECASE)
        if not match:
            continue
        host = _safe_str(match.groupdict().get("host"))
        port = _safe_str(match.groupdict().get("port"))
        database = _safe_str(match.groupdict().get("db"))
        return host, port, database
    return "", "", ""


def _extract_from_mysql_cli(value: str) -> tuple[str, str, str, str]:
    token = _safe_str(value)
    if not token:
        return "", "", "", ""

    host = ""
    port = ""
    user = ""
    database = ""

    host_match = re.search(r"(?:^|\s)-h\s*([a-zA-Z0-9_.-]+)", token)
    if host_match:
        host = _safe_str(host_match.group(1))

    port_match = re.search(r"(?:^|\s)-P\s*(\d{2,5})", token)
    if port_match:
        port = _safe_str(port_match.group(1))

    user_match = re.search(r"(?:^|\s)-u\s*([a-zA-Z0-9_.-]+)", token)
    if user_match:
        user = _safe_str(user_match.group(1))

    db_match = re.search(r"\s([a-zA-Z0-9_.-]+)\s*$", token)
    if db_match:
        candidate = _safe_str(db_match.group(1))
        if candidate not in {"-p"}:
            database = candidate

    return host, port, database, user


def _pick_field_value(fields: list[dict[str, Any]], include_tokens: set[str], key_tokens: tuple[str, ...]) -> str:
    for field in fields:
        context = " ".join(
            [
                _safe_str(field.get("id")),
                _safe_str(field.get("name")),
                _safe_str(field.get("label")),
            ]
        ).lower()
        if include_tokens and not any(token in context for token in include_tokens):
            continue
        if any(token in context for token in key_tokens):
            return _safe_str(field.get("value"))
    return ""


def _field_context(field: dict[str, Any]) -> str:
    return " ".join(
        [
            _safe_str(field.get("id")),
            _safe_str(field.get("name")),
            _safe_str(field.get("label")),
        ]
    ).lower()


def _extract_engine_endpoint(fields: list[dict[str, Any]], engine: str, default_port: str) -> DbEndpoint | None:
    engine_tokens = {engine}
    if engine == "mariadb":
        engine_tokens.add("maria")

    host = _pick_field_value(fields, engine_tokens, ("host", "server"))
    port = _pick_field_value(fields, engine_tokens, ("port",))
    database = _pick_field_value(fields, engine_tokens, ("database", "schema"))
    username = _pick_field_value(fields, engine_tokens, ("user", "login"))
    password = _pick_field_value(fields, engine_tokens, ("password", "pass", "haslo"))

    if not host:
        host = _pick_field_value(fields, set(), (f"{engine} host", "host", "server"))
    if not port:
        port = _pick_field_value(fields, set(), (f"{engine} port", "port"))
    if not database:
        database = _pick_field_value(fields, set(), (f"{engine} database", "database", "schema"))

    url_candidates = [
        _safe_str(field.get("value"))
        for field in fields
        if any(token in _field_context(field) for token in engine_tokens)
        or any(proto in _safe_str(field.get("value")).lower() for proto in [f"jdbc:{engine}", f"{engine}://"])
    ]
    if not url_candidates:
        return None

    for candidate in url_candidates:
        dsn_host, dsn_port, dsn_db = _extract_from_url(candidate)
        if dsn_host and not host:
            host = dsn_host
        if dsn_port and not port:
            port = dsn_port
        if dsn_db and not database:
            database = dsn_db

        cli_host, cli_port, cli_db, cli_user = _extract_from_mysql_cli(candidate)
        if cli_host and not host:
            host = cli_host
        if cli_port and not port:
            port = cli_port
        if cli_db and not database:
            database = cli_db
        if cli_user and not username:
            username = cli_user

    host = _safe_str(host)
    port = _safe_str(port) or default_port
    database = _safe_str(database)
    if not host:
        return None
    return DbEndpoint(
        engine=engine,
        host=host,
        port=port,
        database=database,
        username=_safe_str(username),
        password=_safe_str(password),
    )


def _merge_with_config(vm_id: str, endpoint: DbEndpoint, config: dict[str, Any]) -> DbEndpoint:
    testovki = config.get("testovki") if isinstance(config.get("testovki"), dict) else {}
    defaults = config.get("defaults") if isinstance(config.get("defaults"), dict) else {}
    vm_cfg = (testovki or {}).get(vm_id) if isinstance((testovki or {}).get(vm_id), dict) else {}
    defaults_for_engine = (defaults or {}).get(endpoint.engine)
    engine_defaults = defaults_for_engine if isinstance(defaults_for_engine, dict) else {}
    engine_vm = (vm_cfg or {}).get(endpoint.engine) if isinstance((vm_cfg or {}).get(endpoint.engine), dict) else {}

    username = _safe_str(engine_vm.get("username")) or _safe_str(engine_defaults.get("username")) or endpoint.username
    password = _safe_str(engine_vm.get("password")) or _safe_str(engine_defaults.get("password")) or endpoint.password
    database = _safe_str(engine_vm.get("database_override")) or endpoint.database

    return DbEndpoint(
        engine=endpoint.engine,
        host=endpoint.host,
        port=endpoint.port,
        database=database,
        username=username,
        password=password,
    )


def _mariadb_schema_entries(vm_id: str, endpoint: DbEndpoint, config: dict[str, Any]) -> list[DbEndpoint]:
    testovki = config.get("testovki") if isinstance(config.get("testovki"), dict) else {}
    vm_cfg = (testovki or {}).get(vm_id) if isinstance((testovki or {}).get(vm_id), dict) else {}
    mariadb_cfg = (vm_cfg or {}).get("mariadb") if isinstance((vm_cfg or {}).get("mariadb"), dict) else {}
    schemas_cfg = mariadb_cfg.get("schemas") if isinstance(mariadb_cfg.get("schemas"), list) else []

    if not schemas_cfg:
        return [endpoint]

    out: list[DbEndpoint] = []
    for item in schemas_cfg:
        if not isinstance(item, dict):
            continue
        schema_name = _safe_str(item.get("name"))
        if not schema_name:
            continue
        out.append(
            DbEndpoint(
                engine="mariadb",
                host=endpoint.host,
                port=endpoint.port,
                database=schema_name,
                username=_safe_str(item.get("username")) or endpoint.username,
                password=_safe_str(item.get("password")) or endpoint.password,
            )
        )
    return out or [endpoint]


def _to_dbeaver_provider(engine: str) -> tuple[str, str]:
    if engine == "mariadb":
        return "mariadb", "mariadb"
    return "mysql", "mysql8"


def _connection_name(vm_id: str, endpoint: DbEndpoint) -> str:
    suffix = endpoint.database if endpoint.database else "default"
    return f"{vm_id} | {endpoint.engine.upper()} | {suffix}"


def _to_data_sources_json(entries: list[dict[str, Any]]) -> dict[str, Any]:
    connections: dict[str, Any] = {}
    for row in entries:
        vm_id = _safe_str(row.get("vm_id"))
        endpoint = row.get("endpoint")
        if not isinstance(endpoint, DbEndpoint):
            continue

        provider, driver = _to_dbeaver_provider(endpoint.engine)
        conn_id = f"{driver}-{uuid.uuid4().hex[:24]}"
        jdbc_db = endpoint.database or ""
        jdbc_url = f"jdbc:{provider}://{endpoint.host}:{endpoint.port}/{jdbc_db}"

        connections[conn_id] = {
            "provider": provider,
            "driver": driver,
            "name": _connection_name(vm_id, endpoint),
            "save-password": True,
            "show-system-objects": True,
            "read-only": False,
            "configuration": {
                "host": endpoint.host,
                "port": endpoint.port,
                "database": endpoint.database,
                "url": jdbc_url,
                "type": "dev",
            },
            "user": endpoint.username,
            "password": endpoint.password,
            "description": f"Generated from wizard for VM {vm_id}",
        }

    return {
        "folders": {},
        "connections": connections,
    }


def _write_outputs(out_dir: Path, raw_records: list[dict[str, Any]], exported_rows: list[dict[str, Any]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / "wizard_db_connections.json"
    dbeaver_json_path = out_dir / "dbeaver_data-sources.json"
    dbeaver_csv_path = out_dir / "dbeaver_connections_import.csv"

    serializable_rows: list[dict[str, Any]] = []
    for row in exported_rows:
        endpoint = row.get("endpoint")
        if not isinstance(endpoint, DbEndpoint):
            continue
        serializable_rows.append(
            {
                "vm_id": _safe_str(row.get("vm_id")),
                "env": _safe_str(row.get("env")),
                "engine": endpoint.engine,
                "host": endpoint.host,
                "port": endpoint.port,
                "database": endpoint.database,
                "username": endpoint.username,
                "password": endpoint.password,
                "name": _connection_name(_safe_str(row.get("vm_id")), endpoint),
            }
        )

    raw_dump = {
        "records": raw_records,
        "normalized_connections": serializable_rows,
    }
    raw_path.write_text(json.dumps(raw_dump, ensure_ascii=False, indent=2), encoding="utf-8")

    dbeaver_json = _to_data_sources_json(exported_rows)
    dbeaver_json_path.write_text(json.dumps(dbeaver_json, ensure_ascii=False, indent=2), encoding="utf-8")

    with dbeaver_csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["name", "host", "port", "database", "url", "user", "password", "type"],
        )
        writer.writeheader()
        for row in serializable_rows:
            provider = "mariadb" if row["engine"] == "mariadb" else "mysql"
            writer.writerow(
                {
                    "name": row["name"],
                    "host": row["host"],
                    "port": row["port"],
                    "database": row["database"],
                    "url": f"jdbc:{provider}://{row['host']}:{row['port']}/{row['database']}",
                    "user": row["username"],
                    "password": row["password"],
                    "type": "dev",
                }
            )

    print(f"raw dump: {raw_path}")
    print(f"dbeaver data-sources: {dbeaver_json_path}")
    print(f"dbeaver csv import: {dbeaver_csv_path}")
    print(f"connections generated: {len(serializable_rows)}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse test wizard and export DB connections for DBeaver")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to JSON config")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory")
    parser.add_argument("--vm", default="", help="Optional VM id filter")
    parser.add_argument(
        "--include-host",
        action="append",
        default=[],
        help="Include only hosts matching token (repeatable or comma-separated)",
    )
    parser.add_argument(
        "--exclude-host",
        action="append",
        default=[],
        help="Exclude hosts matching token (repeatable or comma-separated)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config_path = Path(args.config).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    vm_filter = _normalize(args.vm)

    config = _load_config(config_path)
    url, auth_header, headless, timeout_ms = _wizard_settings(config)
    include_host_tokens, exclude_host_tokens = _host_filter_tokens(config=config, args=args)

    pw = None
    browser = None
    try:
        pw, browser, page = _open_wizard(url=url, auth_header=auth_header, headless=headless, timeout_ms=timeout_ms)
        records = _extract_records_from_dom(page)
    finally:
        if browser is not None:
            browser.close()
        if pw is not None:
            pw.stop()

    if not records:
        raise RuntimeError("No wizard records found. Verify auth, URL and page structure.")

    exported_rows: list[dict[str, Any]] = []
    for record in records:
        vm_id = _safe_str(record.get("vm_id"))
        if not vm_id:
            continue
        if vm_filter and _normalize(vm_id) != vm_filter:
            continue

        fields = record.get("fields") if isinstance(record.get("fields"), list) else []
        row_id = _safe_str(record.get("row_id")).lower()
        if row_id.endswith("-mysql-connection"):
            mysql = _extract_engine_endpoint(fields, engine="mysql", default_port="3306")
            if mysql is not None:
                merged_mysql = _merge_with_config(vm_id=vm_id, endpoint=mysql, config=config)
                if _host_allowed(merged_mysql.host, include_host_tokens, exclude_host_tokens):
                    exported_rows.append(
                        {
                            "vm_id": vm_id,
                            "env": _safe_str(record.get("env")),
                            "endpoint": merged_mysql,
                        }
                    )
            continue

        if row_id.endswith("-mariadb-connection"):
            mariadb = _extract_engine_endpoint(fields, engine="mariadb", default_port="3306")
            if mariadb is not None:
                merged_mariadb = _merge_with_config(vm_id=vm_id, endpoint=mariadb, config=config)
                for schema_endpoint in _mariadb_schema_entries(vm_id=vm_id, endpoint=merged_mariadb, config=config):
                    if not _host_allowed(schema_endpoint.host, include_host_tokens, exclude_host_tokens):
                        continue
                    exported_rows.append(
                        {
                            "vm_id": vm_id,
                            "env": _safe_str(record.get("env")),
                            "endpoint": schema_endpoint,
                        }
                    )

    if not exported_rows:
        raise RuntimeError("No MySQL/MariaDB endpoints extracted from wizard DOM.")

    _write_outputs(out_dir=out_dir, raw_records=records, exported_rows=exported_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
