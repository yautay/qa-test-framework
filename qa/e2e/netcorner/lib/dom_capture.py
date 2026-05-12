from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from loguru import logger
from playwright.sync_api import Page

_DOM_CAPTURE_SESSIONS: dict[int, DomCaptureSession] = {}


def _safe_token(value: str, *, fallback: str) -> str:
    text = (value or "").strip().lower()
    if not text:
        return fallback
    normalized = re.sub(r"[^a-z0-9._-]+", "-", text).strip("-")
    return normalized or fallback


def _safe_nodeid(nodeid: str) -> str:
    return _safe_token(nodeid.replace("::", "__").replace("/", "_"), fallback="test")


def _url_token(url: str) -> str:
    parsed = urlparse(url or "")
    token = parsed.path.strip("/") or "root"
    return _safe_token(token.replace("/", "_"), fallback="root")


@dataclass(slots=True)
class DomCaptureSession:
    dom_root: Path
    nodeid: str
    viewport: str
    enabled: bool = False

    def __post_init__(self) -> None:
        self.test_dir = self.dom_root / _safe_nodeid(self.nodeid)
        self.index_path = self.test_dir / "index.jsonl"
        self._hashes: set[str] = set()
        self._seq = 0

        if not self.enabled:
            return

        self.test_dir.mkdir(parents=True, exist_ok=True)
        if self.index_path.is_file():
            try:
                for line in self.index_path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    digest = str(record.get("sha256") or "").strip()
                    if digest:
                        self._hashes.add(digest)
            except Exception as exc:
                logger.warning("dom_capture_index_read_failed path={} error={}", str(self.index_path), str(exc))

        existing = sorted(self.test_dir.glob("*.html.gz"))
        self._seq = len(existing)

    def capture(self, page: Page, *, event: str, page_id: str) -> Path | None:
        if not self.enabled:
            return None

        html = page.content()
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
        if digest in self._hashes:
            return None

        self._hashes.add(digest)
        self._seq += 1

        safe_event = _safe_token(event, fallback="event")
        safe_page_id = _safe_token(page_id, fallback="page")
        safe_url = _url_token(page.url)
        safe_viewport = _safe_token(self.viewport, fallback="viewport")
        file_name = f"{self._seq:03d}__{safe_event}__{safe_page_id}__{safe_url}__{safe_viewport}.html.gz"
        target = self.test_dir / file_name

        with gzip.open(target, mode="wt", encoding="utf-8") as handle:
            handle.write(html)

        record = {
            "sequence": self._seq,
            "event": event,
            "page_id": page_id,
            "url": page.url,
            "viewport": self.viewport,
            "sha256": digest,
            "file": file_name,
            "captured_at": datetime.now(UTC).isoformat(),
        }
        with self.index_path.open(mode="a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        return target


def install_dom_capture_session(
    page: Page,
    *,
    run_root: Path,
    nodeid: str,
    viewport: str,
    enabled: bool,
) -> None:
    dom_root = (run_root / "dom").resolve()
    session = DomCaptureSession(dom_root=dom_root, nodeid=nodeid, viewport=viewport, enabled=enabled)
    _DOM_CAPTURE_SESSIONS[id(page)] = session


def capture_page_dom(page: Page, *, event: str, page_id: str) -> Path | None:
    session = _DOM_CAPTURE_SESSIONS.get(id(page))
    if not isinstance(session, DomCaptureSession):
        return None
    try:
        return session.capture(page, event=event, page_id=page_id)
    except Exception as exc:
        logger.warning(
            "dom_capture_failed nodeid={} page_id={} event={} error={}",
            session.nodeid,
            page_id,
            event,
            str(exc),
        )
        return None
