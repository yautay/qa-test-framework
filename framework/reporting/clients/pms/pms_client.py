from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Any

import requests
from loguru import logger


class PMSClientError(RuntimeError):
    pass


class PMSClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: int,
        health_timeout_seconds: int,
        retry_max: int,
    ) -> None:
        self._base_url = str(base_url or "").rstrip("/")
        self._timeout_seconds = max(1, int(timeout_seconds))
        self._health_timeout_seconds = max(1, int(health_timeout_seconds))
        self._retry_max = max(0, int(retry_max))
        self._session = requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self._base_url)

    @property
    def base_url(self) -> str:
        return self._base_url

    def health(self) -> bool:
        if not self.enabled:
            return False
        url = f"{self._base_url}/health"
        try:
            response = self._session.get(url, timeout=self._health_timeout_seconds)
            ok = bool(response.ok)
            logger.debug("pms_healthcheck", url=url, status_code=response.status_code, ok=ok)
            return ok
        except requests.RequestException as exc:
            logger.warning("pms_healthcheck_failed", url=url, error=str(exc))
            return False

    def get_health(self) -> dict[str, Any]:
        if not self.enabled:
            raise PMSClientError("pms base url is empty")
        url = f"{self._base_url}/health"
        try:
            response = self._session.get(url, timeout=self._health_timeout_seconds)
        except requests.RequestException as exc:
            raise PMSClientError(f"health request failed: GET {url} ({exc})") from exc

        payload: dict[str, Any] = {}
        try:
            raw = response.json()
            if isinstance(raw, dict):
                payload = raw
        except ValueError:
            payload = {}

        error_message = ""
        if not response.ok:
            error_message = str(payload.get("detail") or payload.get("error") or response.text[:500] or "").strip()
            if not error_message:
                error_message = f"status={response.status_code}"

        return {
            "ok": bool(response.ok),
            "status_code": int(response.status_code),
            "payload": payload,
            "error_message": error_message,
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        payload = self._request_json("GET", "/v1/compare/jobs")
        jobs = payload.get("jobs") if isinstance(payload, dict) else []
        if not isinstance(jobs, list):
            return []
        return [job for job in jobs if isinstance(job, dict)]

    def submit_job(
        self,
        *,
        job_id: str,
        pair_id: str,
        metric: str,
        model: str,
        normalize: bool,
        img_a: Path,
        img_b: Path,
    ) -> dict[str, Any]:
        if not img_a.is_file() or not img_b.is_file():
            raise PMSClientError(f"image pair missing: img_a={img_a} img_b={img_b}")

        url = f"{self._base_url}/v1/compare/jobs"
        data = {
            "job_id": str(job_id),
            "pair_id": str(pair_id),
            "metric": str(metric),
            "model": str(model),
            "normalize": "true" if normalize else "false",
        }
        with img_a.open("rb") as fd_a, img_b.open("rb") as fd_b:
            files = {
                "img_a": (img_a.name, fd_a, "image/png"),
                "img_b": (img_b.name, fd_b, "image/png"),
            }
            response = self._request_raw("POST", url, data=data, files=files)

        if response.status_code == 409:
            logger.info("pms_submit_duplicate", job_id=job_id, pair_id=pair_id)
            return {"job_id": job_id, "status": "duplicate"}
        if response.status_code not in {200, 202}:
            raise PMSClientError(f"submit failed: status={response.status_code} body={response.text[:500]}")
        return self._decode_json(response)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request_json("GET", f"/v1/compare/jobs/{job_id}")

    def get_job_error(self, job_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/v1/compare/jobs/{job_id}/error"
        response = self._request_raw("GET", url)
        if response.status_code == 200:
            return self._decode_json(response)

        detail = ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("detail", "") or "").strip()
        except ValueError:
            detail = ""
        if not detail:
            detail = response.text[:500]
        raise PMSClientError(
            f"error details request failed: GET {url} -> {response.status_code} detail={detail or 'unknown'}"
        )

    def download_heatmap(self, job_id: str, output_path: Path) -> bool:
        url = f"{self._base_url}/v1/compare/jobs/{job_id}/heatmap"
        response = self._request_raw("GET", url)
        if response.status_code != 200:
            logger.debug("pms_heatmap_unavailable", job_id=job_id, status_code=response.status_code)
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return True

    def _request_json(self, method: str, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        response = self._request_raw(method, url)
        if not response.ok:
            raise PMSClientError(f"request failed: {method} {url} -> {response.status_code}")
        payload = self._decode_json(response)
        if not isinstance(payload, dict):
            raise PMSClientError(f"invalid response body for {method} {url}")
        return payload

    def _decode_json(self, response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise PMSClientError(f"invalid json response: {exc}") from exc
        if not isinstance(payload, dict):
            raise PMSClientError("json payload is not object")
        return payload

    def _request_raw(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self._session.request(method=method, url=url, timeout=self._timeout_seconds, **kwargs)
                if response.status_code >= 500 or response.status_code == 429:
                    raise PMSClientError(f"retryable status={response.status_code}")
                return response
            except (requests.RequestException, PMSClientError) as exc:
                if attempt > self._retry_max:
                    raise PMSClientError(f"request failed after retries: {method} {url} ({exc})") from exc
                sleep_base = min(8.0, 0.4 * (2 ** (attempt - 1)))
                jitter = random.uniform(0.0, 0.25)
                delay = sleep_base + jitter
                logger.warning(
                    "pms_retry",
                    method=method,
                    url=url,
                    attempt=attempt,
                    retry_max=self._retry_max,
                    delay_sec=round(delay, 3),
                    error=str(exc),
                )
                time.sleep(delay)
