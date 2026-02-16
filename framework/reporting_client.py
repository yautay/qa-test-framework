from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from loguru import logger


@dataclass
class ReportingClient:
    enabled: bool
    base_url: str
    token: str
    run_start_endpoint: str = "/test-run/start"
    test_result_endpoint: str = "/test-run/test-result"
    run_finish_endpoint: str = "/test-run/finish"
    timeout_seconds: int = 5
    retries: int = 2

    def _build_headers(self, payload: dict, json_content_type: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {}
        if json_content_type:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        idempotency_key = payload.get("idempotency_key")
        if isinstance(idempotency_key, str) and idempotency_key.strip():
            headers["X-Idempotency-Key"] = idempotency_key.strip()
        return headers

    @staticmethod
    def _is_failure_with_screenshots(payload: dict) -> bool:
        if payload.get("status") != "failed":
            return False
        artifacts = payload.get("artifacts", {})
        if not isinstance(artifacts, dict):
            return False
        return bool(artifacts.get("screenshot_raw") or artifacts.get("screenshot_annotated"))

    def _post(self, path: str, payload: dict) -> None:
        if not self.enabled or not self.base_url:
            return
        url = f"{self.base_url.rstrip('/')}{path}"
        headers = self._build_headers(payload, json_content_type=True)
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers,
                                         timeout=self.timeout_seconds)
                if response.ok:
                    return
                logger.warning("reporting api non-2xx", status=response.status_code, url=url)
            except Exception as exc:
                logger.warning(f"reporting api call failed: {exc}")
            if attempt < self.retries:
                time.sleep(0.5 * (attempt + 1))

    def _post_test_result_with_screenshots(self, payload: dict) -> None:
        if not self.enabled or not self.base_url:
            return

        url = f"{self.base_url.rstrip('/')}{self.test_result_endpoint}"
        artifacts = payload.get("artifacts", {})
        if not isinstance(artifacts, dict):
            self._post(self.test_result_endpoint, payload)
            return

        raw_path = artifacts.get("screenshot_raw")
        ann_path = artifacts.get("screenshot_annotated")
        file_paths = [p for p in [raw_path, ann_path] if isinstance(p, str) and p]
        existing_paths = [Path(p) for p in file_paths if Path(p).is_file()]
        if not existing_paths:
            self._post(self.test_result_endpoint, payload)
            return

        headers = self._build_headers(payload, json_content_type=False)

        for attempt in range(self.retries + 1):
            files = []
            opened_handles = []
            try:
                for file_path in existing_paths:
                    handle = file_path.open("rb")
                    opened_handles.append(handle)
                    files.append(("screenshots", (file_path.name, handle, "image/png")))

                data = {"payload": json.dumps(payload)}
                response = requests.post(
                    url,
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                if response.ok:
                    return
                logger.warning("reporting api non-2xx", status=response.status_code, url=url)
            except Exception as exc:
                logger.warning(f"reporting screenshot upload failed: {exc}")
            finally:
                for handle in opened_handles:
                    handle.close()

            if attempt < self.retries:
                time.sleep(0.5 * (attempt + 1))

        self._post(self.test_result_endpoint, payload)

    def run_start(self, payload: dict) -> None:
        self._post(self.run_start_endpoint, payload)

    def test_result(self, payload: dict) -> None:
        if self._is_failure_with_screenshots(payload):
            self._post_test_result_with_screenshots(payload)
            return
        self._post(self.test_result_endpoint, payload)

    def run_finish(self, payload: dict) -> None:
        self._post(self.run_finish_endpoint, payload)
