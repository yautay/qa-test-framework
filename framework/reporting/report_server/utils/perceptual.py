from __future__ import annotations

import time
from typing import Any

from framework.reporting.clients.pms import PMSClient, PMSClientError

from ..context import ReportServerContext


def _perceptual_queue_payload(context: ReportServerContext) -> dict[str, Any]:
    if not context.pms_enabled or not str(context.pms_base_url).strip():
        return {
            "enabled": False,
            "base_url": "",
            "server_active": 0,
            "queued": 0,
            "running": 0,
            "done": 0,
            "error": 0,
            "total": 0,
            "updated_at_epoch": int(time.time()),
            "error_message": "pms disabled",
        }

    client = PMSClient(
        base_url=context.pms_base_url,
        timeout_seconds=context.pms_timeout_sec,
        health_timeout_seconds=context.pms_health_timeout_seconds,
        retry_max=context.pms_retry_max,
    )

    try:
        jobs = client.list_jobs()
    except PMSClientError as exc:
        return {
            "enabled": True,
            "base_url": context.pms_base_url,
            "server_active": 0,
            "queued": 0,
            "running": 0,
            "done": 0,
            "error": 0,
            "total": 0,
            "updated_at_epoch": int(time.time()),
            "error_message": str(exc),
        }

    queued = 0
    running = 0
    done = 0
    error = 0
    for job in jobs:
        status = str(job.get("status", "")).strip().lower()
        if status == "queued":
            queued += 1
        elif status == "running":
            running += 1
        elif status == "done":
            done += 1
        elif status == "error":
            error += 1
    return {
        "enabled": True,
        "base_url": context.pms_base_url,
        "server_active": queued + running,
        "queued": queued,
        "running": running,
        "done": done,
        "error": error,
        "total": len(jobs),
        "updated_at_epoch": int(time.time()),
        "error_message": None,
    }


def _perceptual_health_payload(context: ReportServerContext) -> dict[str, Any]:
    checked_at_epoch = int(time.time())
    if not context.pms_enabled:
        return {
            "enabled": False,
            "base_url": "",
            "ok": False,
            "status_code": 0,
            "payload": {},
            "error_message": "PMS disabled in settings.py",
            "reason_code": "pms_disabled",
            "checked_at_epoch": checked_at_epoch,
        }

    if not str(context.pms_base_url).strip():
        return {
            "enabled": True,
            "base_url": "",
            "ok": False,
            "status_code": 0,
            "payload": {},
            "error_message": "PMS_BASE_URL is empty",
            "reason_code": "pms_base_url_missing",
            "checked_at_epoch": checked_at_epoch,
        }

    client = PMSClient(
        base_url=context.pms_base_url,
        timeout_seconds=context.pms_timeout_sec,
        health_timeout_seconds=context.pms_health_timeout_seconds,
        retry_max=context.pms_retry_max,
    )

    try:
        details = client.get_health()
    except PMSClientError as exc:
        return {
            "enabled": True,
            "base_url": context.pms_base_url,
            "ok": False,
            "status_code": 0,
            "payload": {},
            "error_message": str(exc),
            "reason_code": "pms_unreachable",
            "checked_at_epoch": checked_at_epoch,
        }

    payload = details.get("payload") if isinstance(details, dict) else {}
    if not isinstance(payload, dict):
        payload = {}

    return {
        "enabled": True,
        "base_url": context.pms_base_url,
        "ok": bool(details.get("ok")),
        "status_code": int(details.get("status_code", 0) or 0),
        "payload": payload,
        "error_message": str(details.get("error_message") or "").strip() or None,
        "reason_code": None,
        "checked_at_epoch": checked_at_epoch,
    }
