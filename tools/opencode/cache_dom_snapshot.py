from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Error, sync_playwright

from framework.targeting.resolver import resolve_base_url


def _now_token() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _normalize_path(path: str) -> str:
    token = str(path or "").strip()
    if not token:
        return "/"
    if token.startswith(("http://", "https://")):
        parsed = urlparse(token)
        path_part = parsed.path or "/"
        if parsed.query:
            return f"{path_part}?{parsed.query}"
        return path_part
    if not token.startswith("/"):
        token = f"/{token}"
    return token


def _path_slug(path: str) -> str:
    token = _normalize_path(path)
    token = token.replace("?", "__q__").replace("&", "__and__").replace("=", "__eq__")
    token = token.strip("/").replace("/", "__")
    token = re.sub(r"[^a-zA-Z0-9_.-]+", "_", token)
    return token or "root"


def _truncate(text: str, limit: int = 160) -> str:
    token = str(text or "").strip()
    if len(token) <= limit:
        return token
    return token[: limit - 3] + "..."


def _clean(value: Any, *, limit: int = 160) -> str:
    return _truncate(str(value or "").replace("\n", " ").replace("\r", " "), limit=limit)


def _normalize_items(items: Any, *, max_items: int = 120) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []
    output: list[dict[str, str]] = []
    for raw in items[:max_items]:
        if not isinstance(raw, dict):
            continue
        output.append(
            {
                "tag": _clean(raw.get("tag"), limit=40),
                "name": _clean(raw.get("name"), limit=120),
                "id": _clean(raw.get("id"), limit=120),
                "role": _clean(raw.get("role"), limit=60),
                "text": _clean(raw.get("text"), limit=220),
                "href": _clean(raw.get("href"), limit=220),
                "type": _clean(raw.get("type"), limit=60),
            }
        )
    return output


def _extract_dom_summary(page) -> dict[str, Any]:
    raw = page.evaluate(
        """
() => {
  const normalize = (value) => String(value || '').replace(/\\s+/g, ' ').trim();
  const toItem = (el) => ({
    tag: (el.tagName || '').toLowerCase(),
    name: normalize(el.getAttribute('data-name')),
    id: normalize(el.id),
    role: normalize(el.getAttribute('role')),
    text: normalize(el.textContent || el.value || ''),
    href: normalize(el.getAttribute('href')),
    type: normalize(el.getAttribute('type')),
  });

  const pick = (selector, limit = 120) => Array.from(document.querySelectorAll(selector)).slice(0, limit).map(toItem);

  return {
    title: normalize(document.title),
    h1: Array.from(document.querySelectorAll('h1')).map((el) => normalize(el.textContent)).filter(Boolean).slice(0, 12),
    data_name: pick('[data-name]'),
    buttons: pick('button, [role="button"], input[type="submit"], input[type="button"]'),
    links: pick('a[href]'),
    forms: pick('form'),
    inputs: pick('input, textarea, select'),
  };
}
"""
    )

    if not isinstance(raw, dict):
        return {
            "title": "",
            "h1": [],
            "data_name": [],
            "buttons": [],
            "links": [],
            "forms": [],
            "inputs": [],
        }

    return {
        "title": _clean(raw.get("title"), limit=200),
        "h1": [
            _clean(item, limit=200)
            for item in (raw.get("h1") if isinstance(raw.get("h1"), list) else [])[:12]
            if _clean(item, limit=200)
        ],
        "data_name": _normalize_items(raw.get("data_name")),
        "buttons": _normalize_items(raw.get("buttons")),
        "links": _normalize_items(raw.get("links")),
        "forms": _normalize_items(raw.get("forms")),
        "inputs": _normalize_items(raw.get("inputs")),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_digest(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# DOM Digest")
    lines.append("")
    lines.append(f"- Captured at: `{payload.get('captured_at_utc', '')}`")
    lines.append(f"- URL: `{payload.get('url', '')}`")
    lines.append(f"- Title: `{payload.get('title', '')}`")
    if payload.get("h1"):
        lines.append("")
        lines.append("## H1")
        for item in payload.get("h1", []):
            lines.append(f"- {item}")

    def section(name: str, items: list[dict[str, str]], limit: int = 20) -> None:
        if not items:
            return
        lines.append("")
        lines.append(f"## {name}")
        for item in items[:limit]:
            parts = [
                f"tag={item.get('tag', '')}",
                f"data-name={item.get('name', '')}",
                f"id={item.get('id', '')}",
                f"role={item.get('role', '')}",
            ]
            text = item.get("text", "")
            href = item.get("href", "")
            suffix = ""
            if text:
                suffix += f" text={text!r}"
            if href:
                suffix += f" href={href!r}"
            lines.append("- " + ", ".join(parts) + suffix)

    section("Data-name elements", payload.get("data_name", []))
    section("Buttons", payload.get("buttons", []))
    section("Links", payload.get("links", []))
    section("Forms", payload.get("forms", []), limit=10)
    section("Inputs", payload.get("inputs", []), limit=30)

    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _update_index(index_path: Path, *, key: str, entry: dict[str, Any]) -> None:
    if index_path.exists():
        current = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(current, dict):
            current = {}
    else:
        current = {}

    entries = current.get("entries")
    if not isinstance(entries, dict):
        entries = {}
    entries[key] = entry
    current["entries"] = entries
    _write_json(index_path, current)


@dataclass(frozen=True)
class CaptureTarget:
    target_id: str
    server_name: str
    page_path: str
    url: str


def _resolve_target(*, target_id: str, server_name: str, page_path: str) -> CaptureTarget:
    normalized_path = _normalize_path(page_path)
    if page_path.startswith(("http://", "https://")):
        return CaptureTarget(
            target_id=target_id,
            server_name=server_name,
            page_path=normalized_path,
            url=page_path,
        )

    base_url = resolve_base_url(target_id=target_id, server_name=server_name)
    url = urljoin(base_url.rstrip("/") + "/", normalized_path.lstrip("/"))
    return CaptureTarget(
        target_id=target_id,
        server_name=server_name,
        page_path=normalized_path,
        url=url,
    )


def _capture(
    *,
    target: CaptureTarget,
    output_root: Path,
    timeout_ms: int,
    wait_after_load_ms: int,
) -> Path:
    timestamp = _now_token()
    relative_root = Path(target.target_id) / target.server_name / _path_slug(target.page_path)
    history_dir = output_root / relative_root / "history" / timestamp
    latest_dir = output_root / relative_root / "latest"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.goto(target.url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 10_000))
        except Error:
            pass
        if wait_after_load_ms > 0:
            page.wait_for_timeout(wait_after_load_ms)

        summary = _extract_dom_summary(page)
        html = page.content()
        final_url = page.url

        screenshot_path = history_dir / "page.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        context.close()
        browser.close()

    payload = {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "target_id": target.target_id,
        "server_name": target.server_name,
        "path": target.page_path,
        "url": final_url,
        "title": summary.get("title", ""),
        "h1": summary.get("h1", []),
        "data_name": summary.get("data_name", []),
        "buttons": summary.get("buttons", []),
        "links": summary.get("links", []),
        "forms": summary.get("forms", []),
        "inputs": summary.get("inputs", []),
        "files": {
            "html": "page.html",
            "summary": "summary.json",
            "digest": "dom_digest.md",
            "screenshot": "page.png",
        },
    }

    (history_dir / "page.html").write_text(html, encoding="utf-8")
    _write_json(history_dir / "summary.json", payload)
    _write_digest(history_dir / "dom_digest.md", payload)

    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(history_dir, latest_dir)

    key = f"{target.target_id}|{target.server_name}|{target.page_path}"
    _update_index(
        output_root / "index.json",
        key=key,
        entry={
            "target_id": target.target_id,
            "server_name": target.server_name,
            "path": target.page_path,
            "url": final_url,
            "updated_at_utc": payload["captured_at_utc"],
            "latest_dir": str(latest_dir),
            "history_dir": str(history_dir),
        },
    )
    return latest_dir


def capture_dom_snapshot(
    *,
    server_name: str,
    page_path: str,
    target_id: str = "netcorner-nuxt-pl",
    output_root: Path | str = ".opencode/dom-cache",
    timeout_ms: int = 45_000,
    wait_after_load_ms: int = 1_200,
) -> dict[str, Any]:
    target = _resolve_target(target_id=target_id, server_name=server_name, page_path=page_path)
    output_dir = Path(output_root)
    latest_dir = _capture(
        target=target,
        output_root=output_dir,
        timeout_ms=int(timeout_ms),
        wait_after_load_ms=int(wait_after_load_ms),
    )
    summary_path = latest_dir / "summary.json"
    summary_payload: dict[str, Any]
    if summary_path.exists():
        loaded = json.loads(summary_path.read_text(encoding="utf-8"))
        summary_payload = loaded if isinstance(loaded, dict) else {}
    else:
        summary_payload = {}
    return {
        "latest_dir": latest_dir,
        "summary_path": summary_path,
        "digest_path": latest_dir / "dom_digest.md",
        "html_path": latest_dir / "page.html",
        "screenshot_path": latest_dir / "page.png",
        "summary": summary_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture and cache DOM snapshot for OpenCode E2E workflows.")
    parser.add_argument("--server-name", required=True, help="Runtime server selector, for example kadwa.zeta")
    parser.add_argument(
        "--target-id", default="netcorner-nuxt-pl", help="Target id from framework/targeting/registry.py"
    )
    parser.add_argument("--path", default="/", help="Relative path (or absolute URL) to capture")
    parser.add_argument("--output-root", default=".opencode/dom-cache", help="DOM cache output root directory")
    parser.add_argument("--timeout-ms", type=int, default=45_000, help="Navigation timeout in milliseconds")
    parser.add_argument("--wait-after-load-ms", type=int, default=1_200, help="Extra wait after load")
    args = parser.parse_args()

    result = capture_dom_snapshot(
        server_name=args.server_name,
        page_path=args.path,
        target_id=args.target_id,
        output_root=Path(args.output_root),
        timeout_ms=int(args.timeout_ms),
        wait_after_load_ms=int(args.wait_after_load_ms),
    )
    latest_dir = result["latest_dir"]

    print(f"Cached DOM snapshot ready: {latest_dir}")
    print(f"Digest: {latest_dir / 'dom_digest.md'}")
    print(f"Summary: {latest_dir / 'summary.json'}")
    print(f"HTML: {latest_dir / 'page.html'}")
    print(f"Screenshot: {latest_dir / 'page.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
