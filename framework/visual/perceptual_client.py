from __future__ import annotations

"""Client that speaks to the perceptual comparison API when visual perceptual mode is enabled."""

import base64
import time
from pathlib import Path

import requests

from framework.env import RuntimeEnv


class PerceptualServiceError(RuntimeError):
    """Raised when the perceptual API reports a failure or is unreachable."""


class PerceptualClient:
    """Handles availability checks, payload construction, and retries against the perceptual API."""

    def __init__(self, env: RuntimeEnv) -> None:
        self._env = env
        self._checked = False
        self._available = False
        self._consecutive_failures = 0

    @property
    def enabled(self) -> bool:
        """True when the perceptual API endpoint is configured and enabled via RuntimeEnv."""

        return self._env.visual_perceptual_enabled and bool(self._env.visual_perceptual_api_url)

    def ensure_ready(self, required: bool) -> bool:
        """Run a healthcheck once and optionally raise if the service is required but unavailable."""

        if not self.enabled:
            return False
        if self._checked:
            if not self._available and required:
                raise PerceptualServiceError("Perceptual API unavailable and required")
            return self._available

        url = f"{self._env.visual_perceptual_api_url.rstrip('/')}/health"
        try:
            response = requests.get(url, timeout=self._env.visual_perceptual_health_timeout_seconds)
            self._available = response.ok
        except Exception:
            self._available = False
        self._checked = True

        if not self._available and required:
            raise PerceptualServiceError("Perceptual API healthcheck failed and required")
        return self._available

    def _request_payload(self, baseline_path: Path, actual_path: Path) -> dict:
        """Encode screenshots to base64 and attach the configured perceptual options."""

        baseline_b64 = base64.b64encode(baseline_path.read_bytes()).decode("ascii")
        actual_b64 = base64.b64encode(actual_path.read_bytes()).decode("ascii")
        cfg: dict[str, object] = {
            "max_side": self._env.visual_perceptual_max_side,
            "overlay_on": self._env.visual_perceptual_overlay_on,
            "alpha": self._env.visual_perceptual_alpha,
            "lpips_net": self._env.visual_perceptual_lpips_net,
        }
        if self._env.visual_perceptual_force_device:
            cfg["force_device"] = self._env.visual_perceptual_force_device
        return {
            "ref_image_base64": baseline_b64,
            "test_image_base64": actual_b64,
            "config": cfg,
        }

    def compare(self, baseline_path: Path, actual_path: Path) -> dict[str, object]:
        """Invoke the remote compare endpoint and return parsed JSON if successful."""

        if not self.enabled:
            raise PerceptualServiceError("Perceptual API is not enabled")
        if self._consecutive_failures >= self._env.visual_perceptual_fail_fast_errors:
            raise PerceptualServiceError("Perceptual API circuit breaker is open")

        url = f"{self._env.visual_perceptual_api_url.rstrip('/')}/compare"
        payload = self._request_payload(baseline_path, actual_path)

        last_error: Exception | None = None
        for attempt in range(self._env.visual_perceptual_retries + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self._env.visual_perceptual_timeout_seconds,
                )
                if response.ok:
                    self._consecutive_failures = 0
                    return response.json()
                if 400 <= response.status_code < 500:
                    self._consecutive_failures += 1
                    raise PerceptualServiceError(f"Perceptual API 4xx: {response.status_code}")
                last_error = PerceptualServiceError(f"Perceptual API 5xx: {response.status_code}")
            except PerceptualServiceError:
                raise
            except Exception as exc:
                last_error = exc

            if attempt < self._env.visual_perceptual_retries:
                time.sleep(0.5 * (attempt + 1))

        self._consecutive_failures += 1
        raise PerceptualServiceError(f"Perceptual API request failed: {last_error}")
