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
        self._checked_at: float | None = None
        self._available = False
        self._consecutive_failures = 0
        self._session = requests.Session()

    @property
    def enabled(self) -> bool:
        return self._env.visual_perceptual_enabled and bool(self._env.visual_perceptual_api_url)

    def ensure_ready(self, required: bool, *, cache_seconds: int = 30) -> bool:
        """Run a healthcheck and optionally raise if the service is required but unavailable.

        cache_seconds:
            Healthcheck results are cached for this many seconds (per process).
        """
        if not self.enabled:
            return False

        now = time.time()
        if self._checked_at is not None and (now - self._checked_at) < cache_seconds:
            if not self._available and required:
                raise PerceptualServiceError("Perceptual API unavailable and required")
            return self._available

        url = f"{self._env.visual_perceptual_api_url.rstrip('/')}/health"
        try:
            response = self._session.get(url, timeout=self._env.visual_perceptual_health_timeout_seconds)
            self._available = response.ok
        except requests.RequestException:
            self._available = False

        self._checked_at = now

        if not self._available and required:
            raise PerceptualServiceError("Perceptual API healthcheck failed and required")
        return self._available

    def _request_payload(self, baseline_path: Path, actual_path: Path) -> dict:
        """Encode screenshots to base64 and attach the configured perceptual options."""
        try:
            baseline_b64 = base64.b64encode(baseline_path.read_bytes()).decode("ascii")
            actual_b64 = base64.b64encode(actual_path.read_bytes()).decode("ascii")
        except OSError as e:
            raise PerceptualServiceError(f"Unable to read images for perceptual compare: {e}") from e

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
        retries = self._env.visual_perceptual_retries

        for attempt in range(retries + 1):
            try:
                response = self._session.post(
                    url,
                    json=payload,
                    timeout=self._env.visual_perceptual_timeout_seconds,
                )

                if response.ok:
                    self._consecutive_failures = 0
                    try:
                        return response.json()
                    except ValueError as e:
                        self._consecutive_failures += 1
                        raise PerceptualServiceError(f"Perceptual API returned invalid JSON: {e}") from e

                # Rate limit: retryable
                if response.status_code == 429:
                    last_error = PerceptualServiceError("Perceptual API 429 rate limited")
                # Client error: usually not retryable
                elif 400 <= response.status_code < 500:
                    self._consecutive_failures += 1
                    raise PerceptualServiceError(f"Perceptual API 4xx: {response.status_code}")
                else:
                    last_error = PerceptualServiceError(f"Perceptual API 5xx: {response.status_code}")

            except PerceptualServiceError:
                raise
            except requests.RequestException as exc:
                last_error = exc

            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))

        self._consecutive_failures += 1
        raise PerceptualServiceError(f"Perceptual API request failed: {last_error}")
