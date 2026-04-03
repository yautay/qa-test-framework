from __future__ import annotations

"""Build a frozen RuntimeEnv using CLI settings, env vars, and dotenv files."""

import os
from dataclasses import dataclass
from importlib import metadata as importlib_metadata

from dotenv import dotenv_values

import settings
import settings_cli


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


def _resolve_framework_version() -> str:
    """Return framework version from installed package metadata or 'unknown'."""

    try:
        distribution_names = importlib_metadata.packages_distributions().get("framework", [])
    except Exception:
        return "unknown"

    for distribution_name in distribution_names:
        try:
            version = importlib_metadata.version(distribution_name).strip()
        except importlib_metadata.PackageNotFoundError:
            continue
        if version:
            return version

    return "unknown"


@dataclass(frozen=True)
class RuntimeEnv:
    """All runtime knobs that steer browser sessions, reporting, and visual checks."""

    browser: str
    is_grid_available: bool
    grid_provider: str
    grid_ws_endpoint: str
    grid_cdp_endpoint: str
    grid_connect_timeout_ms: int
    headless: bool
    ignore_https_errors: bool
    base_url: str
    server_name: str
    reference_host: str
    record_video: bool
    video_min_seconds: int
    reporting_enabled: bool
    reporting_schema_version: str
    reporting_source_project: str
    reporting_source_origin: str
    reporting_source_producer_id: str
    framework_version: str
    reporting_api_url: str
    reporting_api_token: str
    reporting_api_run_start_endpoint: str
    reporting_api_test_result_endpoint: str
    reporting_api_run_finish_endpoint: str
    reporting_api_bug_endpoint: str
    reporting_api_aso_endpoint: str
    reporting_api_log_endpoint: str
    reporting_api_log_level: str
    reporting_api_timeout_seconds: int
    reporting_api_retries: int
    reporting_async_enabled: bool
    reporting_async_queue_maxsize: int
    reporting_async_max_attempts: int
    reporting_async_max_retry_age_seconds: int
    reporting_async_flush_timeout_seconds: int
    artifacts_dir: str
    allure_enabled: bool
    pytest_html_enabled: bool
    highlight_on_fail: bool
    min_expected_tests: int
    visual_enabled: bool
    visual_compare_mode: str
    visual_baseline_provider: str
    visual_baseline_profile: str
    visual_baseline_version: str
    visual_cache_dir: str
    visual_fail_on_missing_baseline: bool
    visual_freeze_animations: bool
    visual_shift_compensation_y_px: int
    visual_minio_endpoint: str
    visual_minio_access_key: str
    visual_minio_secret_key: str
    visual_minio_bucket: str
    visual_minio_secure: bool
    pms_enabled: bool
    pms_base_url: str
    pms_metric: str
    pms_model: str
    pms_normalize: bool
    pms_submit_rps: float
    pms_poll_rps: float
    pms_max_inflight: int
    pms_server_active_limit: int
    pms_timeout_sec: int
    pms_retry_max: int
    pms_health_timeout_seconds: int
    pms_poll_interval_ms: int
    pms_poll_idle_multiplier: float
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

    settings_headless = bool(settings_cli.is_session_headless)
    settings_grid_available = bool(settings_cli.is_grid_available)
    settings_grid_provider = str(getattr(settings, "grid_provider", "auto"))
    settings_grid_ws_endpoint = settings.grid_ws_endpoint
    settings_grid_cdp_endpoint = str(getattr(settings, "grid_cdp_endpoint", ""))
    settings_grid_connect_timeout_ms = settings.grid_connect_timeout_ms

    configured_browser = env_str(
        "BROWSER",
        str(settings_cli.browser),
    )
    browser = configured_browser.strip().lower()

    reporting_source_origin = env_str(
        "REPORTING_SOURCE_ORIGIN",
        "",
    ).strip()

    if not reporting_source_origin:
        reporting_source_origin = "ci" if os.getenv("CI") else "local"

    server_name = settings_cli.server_name
    reference_host = env_str("REFERENCE_HOST", str(getattr(settings_cli, "reference_host", "")))

    base_url = env_value("BASE_URL") or env_value("BASE_URL_OVERRIDE") or settings_cli.base_url_override or ""

    return RuntimeEnv(
        browser=browser,
        is_grid_available=env_bool("IS_GRID_AVAILABLE", settings_grid_available),
        grid_provider=env_str("GRID_PROVIDER", settings_grid_provider).strip().lower(),
        grid_ws_endpoint=env_str("GRID_WS_ENDPOINT", settings_grid_ws_endpoint),
        grid_cdp_endpoint=env_str("GRID_CDP_ENDPOINT", settings_grid_cdp_endpoint),
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
        server_name=server_name,
        reference_host=reference_host,
        record_video=env_bool("RECORD_VIDEO", bool(settings.record_video)),
        video_min_seconds=env_int("VIDEO_MIN_SECONDS", int(settings.video_min_seconds)),
        reporting_enabled=env_bool("REPORTING_ENABLED", settings.reporting_enabled),
        reporting_schema_version=env_str(
            "REPORTING_SCHEMA_VERSION",
            str(settings.reporting_schema_version),
        ),
        reporting_source_project=env_str(
            "REPORTING_SOURCE_PROJECT",
            str(settings.reporting_source_project),
        ),
        reporting_source_origin=reporting_source_origin,
        reporting_source_producer_id=env_str(
            "REPORTING_SOURCE_PRODUCER_ID",
            str(getattr(settings, "reporting_source_producer_id", "")),
        ).strip(),
        framework_version=_resolve_framework_version(),
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
        reporting_api_bug_endpoint=env_str(
            "REPORTING_API_BUG_ENDPOINT",
            settings.reporting_api_bug_endpoint,
        ),
        reporting_api_aso_endpoint=env_str(
            "REPORTING_API_ASO_ENDPOINT",
            settings.reporting_api_aso_endpoint,
        ),
        reporting_api_log_endpoint=env_str(
            "REPORTING_API_LOG_ENDPOINT",
            settings.reporting_api_log_endpoint,
        ),
        reporting_api_log_level=env_str(
            "REPORTING_API_LOG_LEVEL",
            settings.reporting_api_log_level,
        ),
        reporting_api_timeout_seconds=env_int(
            "REPORTING_API_TIMEOUT_SECONDS",
            settings.reporting_api_timeout_seconds,
        ),
        reporting_api_retries=env_int(
            "REPORTING_API_RETRIES",
            settings.reporting_api_retries,
        ),
        reporting_async_enabled=env_bool(
            "REPORTING_ASYNC_ENABLED",
            bool(settings.reporting_async_enabled),
        ),
        reporting_async_queue_maxsize=env_int(
            "REPORTING_ASYNC_QUEUE_MAXSIZE",
            int(settings.reporting_async_queue_maxsize),
        ),
        reporting_async_max_attempts=env_int(
            "REPORTING_ASYNC_MAX_ATTEMPTS",
            int(settings.reporting_async_max_attempts),
        ),
        reporting_async_max_retry_age_seconds=env_int(
            "REPORTING_ASYNC_MAX_RETRY_AGE_SECONDS",
            int(settings.reporting_async_max_retry_age_seconds),
        ),
        reporting_async_flush_timeout_seconds=env_int(
            "REPORTING_ASYNC_FLUSH_TIMEOUT_SECONDS",
            int(settings.reporting_async_flush_timeout_seconds),
        ),
        artifacts_dir=env_str("ARTIFACTS_DIR", settings.artifacts_dir),
        allure_enabled=env_bool("ALLURE_ENABLED", bool(settings.allure_enabled)),
        pytest_html_enabled=env_bool("PYTEST_HTML_ENABLED", bool(settings.pytest_html_enabled)),
        highlight_on_fail=env_bool("HIGHLIGHT_ON_FAIL", settings.highlight_on_fail),
        min_expected_tests=env_int("MIN_EXPECTED_TESTS", settings.min_expected_tests),
        visual_enabled=env_bool(
            "VISUAL_ENABLED",
            bool(settings.visual_enabled),
        ),
        visual_compare_mode=env_str(
            "VISUAL_COMPARE_MODE",
            str(settings.visual_compare_mode),
        )
        .strip()
        .lower(),
        visual_baseline_provider=env_str(
            "VISUAL_BASELINE_PROVIDER",
            str(settings.visual_baseline_provider),
        )
        .strip()
        .lower(),
        visual_baseline_profile=env_str(
            "VISUAL_BASELINE_PROFILE",
            str(settings.visual_baseline_profile),
        ),
        visual_baseline_version=env_str(
            "VISUAL_BASELINE_VERSION",
            str(settings.visual_baseline_version),
        ),
        visual_cache_dir=env_str(
            "VISUAL_CACHE_DIR",
            str(settings.visual_cache_dir),
        ),
        visual_fail_on_missing_baseline=env_bool(
            "VISUAL_FAIL_ON_MISSING_BASELINE",
            bool(settings.visual_fail_on_missing_baseline),
        ),
        visual_freeze_animations=env_bool(
            "VISUAL_FREEZE_ANIMATIONS",
            bool(getattr(settings, "visual_freeze_animations", True)),
        ),
        visual_shift_compensation_y_px=env_int(
            "VISUAL_SHIFT_COMPENSATION_Y_PX",
            int(getattr(settings, "visual_shift_compensation_y_px", 0)),
        ),
        visual_minio_endpoint=env_str(
            "VISUAL_MINIO_ENDPOINT",
            str(settings.visual_minio_endpoint),
        ),
        visual_minio_access_key=env_str(
            "VISUAL_MINIO_ACCESS_KEY",
            str(settings.visual_minio_access_key),
        ),
        visual_minio_secret_key=env_str(
            "VISUAL_MINIO_SECRET_KEY",
            str(settings.visual_minio_secret_key),
        ),
        visual_minio_bucket=env_str(
            "VISUAL_MINIO_BUCKET",
            str(settings.visual_minio_bucket),
        ),
        visual_minio_secure=env_bool(
            "VISUAL_MINIO_SECURE",
            bool(settings.visual_minio_secure),
        ),
        pms_enabled=env_bool(
            "PMS_ENABLED",
            bool(settings.pms_enabled),
        ),
        pms_base_url=env_str(
            "PMS_BASE_URL",
            str(settings.pms_base_url),
        ),
        pms_metric=env_str(
            "PMS_METRIC",
            str(settings.pms_metric),
        )
        .strip()
        .lower(),
        pms_model=env_str(
            "PMS_MODEL",
            str(settings.pms_model),
        )
        .strip()
        .lower(),
        pms_normalize=env_bool(
            "PMS_NORMALIZE",
            bool(settings.pms_normalize),
        ),
        pms_submit_rps=env_float(
            "PMS_SUBMIT_RPS",
            float(settings.pms_submit_rps),
        ),
        pms_poll_rps=env_float(
            "PMS_POLL_RPS",
            float(settings.pms_poll_rps),
        ),
        pms_max_inflight=env_int(
            "PMS_MAX_INFLIGHT",
            int(settings.pms_max_inflight),
        ),
        pms_server_active_limit=env_int(
            "PMS_SERVER_ACTIVE_LIMIT",
            int(settings.pms_server_active_limit),
        ),
        pms_timeout_sec=env_int(
            "PMS_TIMEOUT_SEC",
            int(settings.pms_timeout_sec),
        ),
        pms_retry_max=env_int(
            "PMS_RETRY_MAX",
            int(settings.pms_retry_max),
        ),
        pms_health_timeout_seconds=env_int(
            "PMS_HEALTH_TIMEOUT_SECONDS",
            int(settings.pms_health_timeout_seconds),
        ),
        pms_poll_interval_ms=env_int(
            "PMS_POLL_INTERVAL_MS",
            int(settings.pms_poll_interval_ms),
        ),
        pms_poll_idle_multiplier=env_float(
            "PMS_POLL_IDLE_MULTIPLIER",
            float(settings.pms_poll_idle_multiplier),
        ),
        visual_uncertain_enabled=env_bool(
            "VISUAL_UNCERTAIN_ENABLED",
            bool(settings.visual_uncertain_enabled),
        ),
        visual_uncertain_pixel_delta=env_float(
            "VISUAL_UNCERTAIN_PIXEL_DELTA",
            float(settings.visual_uncertain_pixel_delta),
        ),
        visual_uncertain_lpips_delta=env_float(
            "VISUAL_UNCERTAIN_LPIPS_DELTA",
            float(settings.visual_uncertain_lpips_delta),
        ),
        visual_uncertain_dists_delta=env_float(
            "VISUAL_UNCERTAIN_DISTS_DELTA",
            float(settings.visual_uncertain_dists_delta),
        ),
    )
