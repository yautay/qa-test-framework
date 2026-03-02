from __future__ import annotations

from pathlib import Path
from secrets import token_urlsafe
from typing import Any, cast
import json
import re
import time


LOCK_TTL_SECONDS = 110
TEXT_MAX_LENGTH = 500
_TEXT_CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _normalize_text(value: Any, *, trim: bool = True) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _TEXT_CONTROL_CHAR_REGEX.sub("", normalized)
    if trim:
        normalized = normalized.strip()
    return normalized


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _lock_file_path(build_dir: Path) -> Path:
    return build_dir / "build.lock.json"


def _read_lock(build_dir: Path) -> dict[str, Any] | None:
    lock_path = _lock_file_path(build_dir)
    if not lock_path.is_file():
        return None
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _is_lock_expired(lock_data: dict[str, Any], now: float) -> bool:
    try:
        return float(lock_data.get("expires_at", 0)) <= now
    except Exception:
        return True


def _write_lock(build_dir: Path, payload: dict[str, Any]) -> None:
    _atomic_write_json(_lock_file_path(build_dir), payload)


def _acquire_lock(
    build_dir: Path,
    client_id: str,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    timestamp = time.time() if now is None else float(now)
    existing = _read_lock(build_dir)
    if existing and not _is_lock_expired(existing, timestamp):
        if str(existing.get("owner_client_id", "")) != client_id:
            return {"accepted": False, "reason": "locked", "lock": existing}
        lock_id = str(existing.get("lock_id") or "") or token_urlsafe(12)
        updated = {
            "build_id": str(existing.get("build_id") or ""),
            "lock_id": lock_id,
            "owner_client_id": client_id,
            "created_at": float(existing.get("created_at") or timestamp),
            "last_heartbeat_at": timestamp,
            "expires_at": timestamp + LOCK_TTL_SECONDS,
        }
        _write_lock(build_dir, updated)
        return {"accepted": True, "lock": updated}

    lock_id = token_urlsafe(12)
    payload = {
        "build_id": build_dir.name,
        "lock_id": lock_id,
        "owner_client_id": client_id,
        "created_at": timestamp,
        "last_heartbeat_at": timestamp,
        "expires_at": timestamp + LOCK_TTL_SECONDS,
    }
    _write_lock(build_dir, payload)
    return {"accepted": True, "lock": payload}


def _heartbeat_lock(
    build_dir: Path,
    client_id: str,
    lock_id: str,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    timestamp = time.time() if now is None else float(now)
    existing = _read_lock(build_dir)
    if not existing or _is_lock_expired(existing, timestamp):
        return {"accepted": False, "reason": "expired"}
    if str(existing.get("owner_client_id", "")) != client_id:
        return {"accepted": False, "reason": "owner_mismatch", "lock": existing}
    if str(existing.get("lock_id", "")) != lock_id:
        return {"accepted": False, "reason": "lock_mismatch", "lock": existing}
    updated = {
        "build_id": str(existing.get("build_id") or build_dir.name),
        "lock_id": lock_id,
        "owner_client_id": client_id,
        "created_at": float(existing.get("created_at") or timestamp),
        "last_heartbeat_at": timestamp,
        "expires_at": timestamp + LOCK_TTL_SECONDS,
    }
    _write_lock(build_dir, updated)
    return {"accepted": True, "lock": updated}


def _release_lock(build_dir: Path, client_id: str, lock_id: str) -> dict[str, Any]:
    existing = _read_lock(build_dir)
    if not existing:
        return {"accepted": True}
    if str(existing.get("owner_client_id", "")) != client_id:
        return {"accepted": False, "reason": "owner_mismatch"}
    if str(existing.get("lock_id", "")) != lock_id:
        return {"accepted": False, "reason": "lock_mismatch"}
    try:
        _lock_file_path(build_dir).unlink(missing_ok=True)
    except Exception:
        pass
    return {"accepted": True}


def _state_file_path(build_dir: Path) -> Path:
    return build_dir / "state.json"


def _empty_case_state() -> dict[str, Any]:
    return {
        "bug": {"locked": False, "synced": False, "note": ""},
        "aso": {"locked": False, "synced": False, "note": ""},
    }


def _normalize_case_state(raw: Any) -> dict[str, Any]:
    base = raw if isinstance(raw, dict) else {}
    bug = cast(dict[str, Any], base.get("bug")) if isinstance(base.get("bug"), dict) else {}
    aso = cast(dict[str, Any], base.get("aso")) if isinstance(base.get("aso"), dict) else {}
    bug_note = _normalize_text(bug.get("note"), trim=True)[:TEXT_MAX_LENGTH]
    aso_note = _normalize_text(aso.get("note"), trim=True)[:TEXT_MAX_LENGTH]
    return {
        "bug": {"locked": bool(bug.get("locked", False)), "synced": bool(bug.get("synced", False)), "note": bug_note},
        "aso": {"locked": bool(aso.get("locked", False)), "synced": bool(aso.get("synced", False)), "note": aso_note},
    }


def _normalize_outbox_entry(raw: Any) -> dict[str, Any]:
    base = raw if isinstance(raw, dict) else {}
    payload = base.get("payload") if isinstance(base.get("payload"), dict) else {}
    return {
        "event_id": str(base.get("event_id", "")),
        "type": str(base.get("type", "")),
        "payload": payload,
        "status": str(base.get("status", "pending")),
        "attempts": int(base.get("attempts", 0) or 0),
        "last_attempt_at": str(base.get("last_attempt_at", "")),
        "sent_at": str(base.get("sent_at", "")),
        "last_error": str(base.get("last_error", "")),
        "test_case_id": str(base.get("test_case_id", "")),
    }


def _load_state(build_dir: Path) -> dict[str, Any]:
    state_path = _state_file_path(build_dir)
    if not state_path.is_file():
        return {"test_cases": {}, "outbox": []}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"test_cases": {}, "outbox": []}
    if not isinstance(data, dict):
        return {"test_cases": {}, "outbox": []}
    test_cases = cast(dict[str, Any], data.get("test_cases")) if isinstance(data.get("test_cases"), dict) else {}
    outbox = cast(list[dict[str, Any]], data.get("outbox")) if isinstance(data.get("outbox"), list) else []
    normalized_cases: dict[str, Any] = {}
    for key, value in test_cases.items():
        if not isinstance(key, str):
            continue
        normalized_cases[key] = _normalize_case_state(value)
    normalized_outbox = [_normalize_outbox_entry(item) for item in outbox if isinstance(item, dict)]
    return {"test_cases": normalized_cases, "outbox": normalized_outbox}


def _save_state(build_dir: Path, state: dict[str, Any]) -> None:
    _atomic_write_json(_state_file_path(build_dir), state)


def _ensure_case_state(state: dict[str, Any], case_id: str) -> dict[str, Any]:
    cases = state.setdefault("test_cases", {})
    existing = cases.get(case_id)
    if isinstance(existing, dict):
        normalized = _normalize_case_state(existing)
        cases[case_id] = normalized
        return normalized
    normalized = _empty_case_state()
    cases[case_id] = normalized
    return normalized


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _record_event_attempt(event: dict[str, Any], accepted: bool, error: str) -> None:
    timestamp = _utc_timestamp()
    event["attempts"] = int(event.get("attempts", 0) or 0) + 1
    event["last_attempt_at"] = timestamp
    if accepted:
        event["status"] = "sent"
        event["sent_at"] = timestamp
        event["last_error"] = ""
    else:
        event["status"] = "failed"
        event["last_error"] = error


def _is_reporting_tag_event(event_type: str) -> bool:
    return event_type in {"BUG_SET", "ASO_SET"}


def _treat_reporting_disabled_as_success(state: dict[str, Any]) -> tuple[int, int]:
    synced_cases = 0
    sent_events = 0

    test_cases = state.get("test_cases", {})
    if isinstance(test_cases, dict):
        for case_id, _raw_case in test_cases.items():
            if not isinstance(case_id, str):
                continue
            case_state = _ensure_case_state(state, case_id)
            bug = case_state.get("bug", {}) if isinstance(case_state.get("bug"), dict) else {}
            aso = case_state.get("aso", {}) if isinstance(case_state.get("aso"), dict) else {}

            changed = False
            if bool(bug.get("locked")) and not bool(bug.get("synced")):
                case_state["bug"]["synced"] = True
                changed = True
            if bool(aso.get("locked")) and not bool(aso.get("synced")):
                case_state["aso"]["synced"] = True
                changed = True
            if changed:
                synced_cases += 1

    outbox = state.get("outbox", [])
    if isinstance(outbox, list):
        for entry in outbox:
            if not isinstance(entry, dict):
                continue
            event_type = str(entry.get("type", "")).upper()
            if not _is_reporting_tag_event(event_type):
                continue
            status = str(entry.get("status", "pending")).lower()
            if status in {"sent", "superseded"}:
                continue
            _record_event_attempt(entry, True, "")
            sent_events += 1

    return synced_cases, sent_events
