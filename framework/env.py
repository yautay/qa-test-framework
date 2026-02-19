from __future__ import annotations

"""Build a frozen RuntimeEnv using CLI settings, env vars, and dotenv files."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import dotenv_values

import settings_cli
import settings


def _as_bool(value: str | None, default: bool) -> bool:
    """Interpret common truthy/falsey tokens and fall back to the provided default."""

    if value is None:
        return default

    token = value.strip().lower()
    if token == "":
        return default

    truthy = {"1", "true", "t", "yes", "y", "on"}
    falsey = {"0", "false", "f", "no", "n", "off"}

    if token in truthy:
        return True
    if token in falsey:
        return False

    return default


def _load_dotenv_file(env_file: str = ".env") -> dict[str, str]:
    """Parse a dotenv-style file into a string dictionary, ignoring comments."""
    return {k: v for k, v in dotenv_values(env_file).items() if v is not None}


@dataclass(frozen=True)
class RuntimeEnv:
    """All runtime knobs that steer browser sessions, reporting, and visual checks."""

    browser: str
    is_grid_available: bool
    grid_ws_endpoint: str
    grid_connect_timeout_ms: int
    headless: bool
    ignore_https_errors: bool
    base_url: str
    server_type: str
    server_name: str
    record_video: bool
    video_min_seconds: int
    reporting_enabled: bool
    reporting_schema_version: str
    reporting_source_project: str
    reporting_source_origin: str
    framework_version: str
    reporting_api_url: str
    reporting_api_token: str
    reporting_api_run_start_endpoint: str
    reporting_api_test_result_endpoint: str
    reporting_api_run_finish_endpoint: str
    reporting_api_timeout_seconds: int
    reporting_api_retries: int
    artifacts_dir: str
    highlight_on_fail: bool
    min_expected_tests: int
    visual_enabled: bool
    visual_compare_mode: str
    visual_baseline_provider: str
    visual_baseline_profile: str
    visual_baseline_version: str
    visual_cache_dir: str
    visual_fail_on_missing_baseline: bool
    visual_warn_as_fail: bool
    visual_minio_endpoint: str
    visual_minio_access_key: str
    visual_minio_secret_key: str
    visual_minio_bucket: str
    visual_minio_secure: bool
    visual_perceptual_enabled: bool
    visual_perceptual_required: bool
    visual_perceptual_api_url: str
    visual_perceptual_timeout_seconds: int
    visual_perceptual_health_timeout_seconds: int
    visual_perceptual_retries: int
    visual_perceptual_fail_fast_errors: int
    visual_perceptual_fallback_mode: str
    visual_perceptual_force_device: str
    visual_perceptual_max_side: int
    visual_perceptual_overlay_on: str
    visual_perceptual_alpha: float
    visual_perceptual_lpips_net: str
    visual_uncertain_enabled: bool
    visual_uncertain_pixel_delta: float
    visual_uncertain_lpips_delta: float
    visual_uncertain_dists_delta: float


def load_env() -> RuntimeEnv:
    """Construct RuntimeEnv by combining os.environ, dotenv, and settings defaults."""

    dotenv_map = _load_dotenv_file()

    def env_value(name: str, default: str | None = None) -> str | None:
        if name in os.environ:
            return os.environ[name]
        if name in dotenv_map:
            return dotenv_map[name]
        return default

    # --- typed helpers -------------------------------------------------

    def env_str(name: str, default: str) -> str:
        v = env_value(name)
        return default if v is None else v

    def env_int(name: str, default: int) -> int:
        v = env_value(name)
        return default if v is None or v.strip() == "" else int(v)

    def env_float(name: str, default: float) -> float:
        v = env_value(name)
        return default if v is None or v.strip() == "" else float(v)

    def env_bool(name: str, default: bool) -> bool:
        return _as_bool(env_value(name), default)

    # --- defaults from settings ----------------------------------------

    settings_headless = bool(getattr(settings, "is_session_headless", True))
    settings_grid_available = bool(getattr(settings, "is_grid_available", False))
    settings_grid_ws_endpoint = str(getattr(settings, "grid_ws_endpoint", "ws://127.0.0.1:9323/"))
    settings_grid_connect_timeout_ms = int(getattr(settings, "grid_connect_timeout_ms", 30000))

    configured_browser = env_str(
        "BROWSER",
        str(getattr(settings, "browser", "chromium")),
    )
    browser = configured_browser.strip().lower()

    reporting_source_origin = env_str(
        "REPORTING_SOURCE_ORIGIN",
        str(getattr(settings, "reporting_source_origin", "")),
    ).strip()

    if not reporting_source_origin:
        reporting_source_origin = "ci" if os.getenv("CI") else "local"

    server_type = settings_cli.server_type
    server_name = settings_cli.server_name

    base_url = env_value("BASE_URL") or env_value("BASE_URL_OVERRIDE") or settings_cli.base_url_override or ""

    return RuntimeEnv(
        browser=browser,
        is_grid_available=env_bool("IS_GRID_AVAILABLE", settings_grid_available),
        grid_ws_endpoint=env_str("GRID_WS_ENDPOINT", settings_grid_ws_endpoint),
        grid_connect_timeout_ms=env_int(
            "GRID_CONNECT_TIMEOUT_MS",
            settings_grid_connect_timeout_ms,
        ),
        headless=env_bool("HEADLESS", settings_headless),
        ignore_https_errors=env_bool(
            "IGNORE_HTTPS_ERRORS",
            settings.ignore_https_errors,
        ),
        base_url=base_url,
        server_type=server_type,
        server_name=server_name,
        record_video=env_bool("RECORD_VIDEO", True),
        video_min_seconds=env_int("VIDEO_MIN_SECONDS", 30),
        reporting_enabled=env_bool("REPORTING_ENABLED", settings.reporting_enabled),
        reporting_schema_version=env_str(
            "REPORTING_SCHEMA_VERSION",
            str(getattr(settings, "reporting_schema_version", "2.0")),
        ),
        reporting_source_project=env_str(
            "REPORTING_SOURCE_PROJECT",
            str(getattr(settings, "reporting_source_project", Path.cwd().name)),
        ),
        reporting_source_origin=reporting_source_origin,
        framework_version=env_str(
            "FRAMEWORK_VERSION",
            str(getattr(settings, "framework_version", "1.0.0")),
        ),
        reporting_api_url=env_str("REPORTING_API_URL", settings.reporting_api_url),
        reporting_api_token=env_str("REPORTING_API_TOKEN", settings.reporting_api_token),
        reporting_api_run_start_endpoint=env_str(
            "REPORTING_API_RUN_START_ENDPOINT",
            settings.reporting_api_run_start_endpoint,
        ),
        reporting_api_test_result_endpoint=env_str(
            "REPORTING_API_TEST_RESULT_ENDPOINT",
            settings.reporting_api_test_result_endpoint,
        ),
        reporting_api_run_finish_endpoint=env_str(
            "REPORTING_API_RUN_FINISH_ENDPOINT",
            settings.reporting_api_run_finish_endpoint,
        ),
        reporting_api_timeout_seconds=env_int(
            "REPORTING_API_TIMEOUT_SECONDS",
            settings.reporting_api_timeout_seconds,
        ),
        reporting_api_retries=env_int(
            "REPORTING_API_RETRIES",
            settings.reporting_api_retries,
        ),
        artifacts_dir=env_str("ARTIFACTS_DIR", "artifacts"),
        highlight_on_fail=env_bool("HIGHLIGHT_ON_FAIL", True),
        min_expected_tests=env_int("MIN_EXPECTED_TESTS", 1),
        visual_enabled=env_bool(
            "VISUAL_ENABLED",
            bool(getattr(settings, "visual_enabled", False)),
        ),
        visual_compare_mode=env_str(
            "VISUAL_COMPARE_MODE",
            str(getattr(settings, "visual_compare_mode", "hybrid")),
        )
        .strip()
        .lower(),
        visual_baseline_provider=env_str(
            "VISUAL_BASELINE_PROVIDER",
            str(getattr(settings, "visual_baseline_provider", "minio")),
        )
        .strip()
        .lower(),
        visual_baseline_profile=env_str(
            "VISUAL_BASELINE_PROFILE",
            str(getattr(settings, "visual_baseline_profile", "test-ref")),
        ),
        visual_baseline_version=env_str(
            "VISUAL_BASELINE_VERSION",
            str(getattr(settings, "visual_baseline_version", "latest")),
        ),
        visual_cache_dir=env_str(
            "VISUAL_CACHE_DIR",
            str(getattr(settings, "visual_cache_dir", ".visual_cache")),
        ),
        visual_fail_on_missing_baseline=env_bool(
            "VISUAL_FAIL_ON_MISSING_BASELINE",
            bool(getattr(settings, "visual_fail_on_missing_baseline", False)),
        ),
        visual_warn_as_fail=env_bool(
            "VISUAL_WARN_AS_FAIL",
            bool(getattr(settings, "visual_warn_as_fail", False)),
        ),
        visual_minio_endpoint=env_str(
            "VISUAL_MINIO_ENDPOINT",
            str(getattr(settings, "visual_minio_endpoint", "")),
        ),
        visual_minio_access_key=env_str(
            "VISUAL_MINIO_ACCESS_KEY",
            str(getattr(settings, "visual_minio_access_key", "")),
        ),
        visual_minio_secret_key=env_str(
            "VISUAL_MINIO_SECRET_KEY",
            str(getattr(settings, "visual_minio_secret_key", "")),
        ),
        visual_minio_bucket=env_str(
            "VISUAL_MINIO_BUCKET",
            str(getattr(settings, "visual_minio_bucket", "visual-baselines")),
        ),
        visual_minio_secure=env_bool(
            "VISUAL_MINIO_SECURE",
            bool(getattr(settings, "visual_minio_secure", True)),
        ),
        visual_perceptual_enabled=env_bool(
            "VISUAL_PERCEPTUAL_ENABLED",
            bool(getattr(settings, "visual_perceptual_enabled", False)),
        ),
        visual_perceptual_required=env_bool(
            "VISUAL_PERCEPTUAL_REQUIRED",
            bool(getattr(settings, "visual_perceptual_required", False)),
        ),
        visual_perceptual_api_url=env_str(
            "VISUAL_PERCEPTUAL_API_URL",
            str(getattr(settings, "visual_perceptual_api_url", "")),
        ),
        visual_perceptual_timeout_seconds=env_int(
            "VISUAL_PERCEPTUAL_TIMEOUT_SECONDS",
            int(getattr(settings, "visual_perceptual_timeout_seconds", 15)),
        ),
        visual_perceptual_health_timeout_seconds=env_int(
            "VISUAL_PERCEPTUAL_HEALTH_TIMEOUT_SECONDS",
            int(getattr(settings, "visual_perceptual_health_timeout_seconds", 2)),
        ),
        visual_perceptual_retries=env_int(
            "VISUAL_PERCEPTUAL_RETRIES",
            int(getattr(settings, "visual_perceptual_retries", 2)),
        ),
        visual_perceptual_fail_fast_errors=env_int(
            "VISUAL_PERCEPTUAL_FAIL_FAST_ERRORS",
            int(getattr(settings, "visual_perceptual_fail_fast_errors", 3)),
        ),
        visual_perceptual_fallback_mode=env_str(
            "VISUAL_PERCEPTUAL_FALLBACK_MODE",
            str(getattr(settings, "visual_perceptual_fallback_mode", "pixel")),
        )
        .strip()
        .lower(),
        visual_perceptual_force_device=env_str(
            "VISUAL_PERCEPTUAL_FORCE_DEVICE",
            str(getattr(settings, "visual_perceptual_force_device", "")),
        )
        .strip()
        .lower(),
        visual_perceptual_max_side=env_int(
            "VISUAL_PERCEPTUAL_MAX_SIDE",
            int(getattr(settings, "visual_perceptual_max_side", 1024)),
        ),
        visual_perceptual_overlay_on=env_str(
            "VISUAL_PERCEPTUAL_OVERLAY_ON",
            str(getattr(settings, "visual_perceptual_overlay_on", "test")),
        )
        .strip()
        .lower(),
        visual_perceptual_alpha=env_float(
            "VISUAL_PERCEPTUAL_ALPHA",
            float(getattr(settings, "visual_perceptual_alpha", 0.45)),
        ),
        visual_perceptual_lpips_net=env_str(
            "VISUAL_PERCEPTUAL_LPIPS_NET",
            str(getattr(settings, "visual_perceptual_lpips_net", "vgg")),
        )
        .strip()
        .lower(),
        visual_uncertain_enabled=env_bool(
            "VISUAL_UNCERTAIN_ENABLED",
            bool(getattr(settings, "visual_uncertain_enabled", True)),
        ),
        visual_uncertain_pixel_delta=env_float(
            "VISUAL_UNCERTAIN_PIXEL_DELTA",
            float(getattr(settings, "visual_uncertain_pixel_delta", 0.001)),
        ),
        visual_uncertain_lpips_delta=env_float(
            "VISUAL_UNCERTAIN_LPIPS_DELTA",
            float(getattr(settings, "visual_uncertain_lpips_delta", 0.01)),
        ),
        visual_uncertain_dists_delta=env_float(
            "VISUAL_UNCERTAIN_DISTS_DELTA",
            float(getattr(settings, "visual_uncertain_dists_delta", 0.01)),
        ),
    )
