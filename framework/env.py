from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
import settings_cli
import settings


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip() in {"1", "true", "True", "yes", "on"}


def _load_dotenv_file(env_file: str = ".env") -> dict[str, str]:
    path = Path(env_file)
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


@dataclass(frozen=True)
class RuntimeEnv:
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


def load_env() -> RuntimeEnv:
    dotenv_values = _load_dotenv_file()

    def env_value(name: str, default: str | None = None) -> str | None:
        if name in os.environ:
            return os.environ[name]
        if name in dotenv_values:
            return dotenv_values[name]
        return default

    settings_headless = bool(getattr(settings, "is_session_headless", True))
    settings_grid_available = bool(
        getattr(settings, "is_grid_available", getattr(settings, "is_grid_available", False))
    )
    settings_grid_ws_endpoint = str(
        getattr(settings, "grid_ws_endpoint", getattr(settings, "grid_ws_endpoint", "ws://127.0.0.1:9323/"))
    )
    settings_grid_connect_timeout_ms = int(
        getattr(
            settings,
            "grid_connect_timeout_ms",
            getattr(settings, "grid_connect_timeout_ms", 30000),
        )
    )
    configured_browser = env_value("BROWSER", getattr(settings, "browser", "chromium")) or "chromium"
    browser = configured_browser.strip().lower()
    reporting_source_origin = (
            env_value("REPORTING_SOURCE_ORIGIN", getattr(settings, "reporting_source_origin", "")) or ""
    )
    if not reporting_source_origin:
        reporting_source_origin = "ci" if os.getenv("CI") else "local"
    server_type = settings_cli.server_type
    server_name = settings_cli.server_name

    base_url = env_value("BASE_URL") or env_value("BASE_URL_OVERRIDE") or settings_cli.base_url_override or ""

    return RuntimeEnv(
        browser=browser,
        is_grid_available=_as_bool(env_value("IS_GRID_AVAILABLE"), settings_grid_available),
        grid_ws_endpoint=env_value("GRID_WS_ENDPOINT", settings_grid_ws_endpoint) or settings_grid_ws_endpoint,
        grid_connect_timeout_ms=int(
            env_value("GRID_CONNECT_TIMEOUT_MS", str(settings_grid_connect_timeout_ms))
            or str(settings_grid_connect_timeout_ms)
        ),
        headless=_as_bool(env_value("HEADLESS"), settings_headless),
        ignore_https_errors=_as_bool(env_value("IGNORE_HTTPS_ERRORS"), settings.ignore_https_errors),
        base_url=base_url,
        server_type=server_type,
        server_name=server_name,
        record_video=_as_bool(env_value("RECORD_VIDEO"), True),
        video_min_seconds=int(env_value("VIDEO_MIN_SECONDS", "30") or "30"),
        reporting_enabled=_as_bool(env_value("REPORTING_ENABLED"), settings.reporting_enabled),
        reporting_schema_version=env_value(
            "REPORTING_SCHEMA_VERSION",
            getattr(settings, "reporting_schema_version", "2.0"),
        )
                                 or "2.0",
        reporting_source_project=env_value(
            "REPORTING_SOURCE_PROJECT",
            getattr(settings, "reporting_source_project", Path.cwd().name),
        )
                                 or Path.cwd().name,
        reporting_source_origin=reporting_source_origin,
        framework_version=env_value(
            "FRAMEWORK_VERSION",
            getattr(settings, "framework_version", "1.0.0"),
        )
                          or "1.0.0",
        reporting_api_url=env_value("REPORTING_API_URL", settings.reporting_api_url) or "",
        reporting_api_token=env_value("REPORTING_API_TOKEN", settings.reporting_api_token) or "",
        reporting_api_run_start_endpoint=env_value(
            "REPORTING_API_RUN_START_ENDPOINT",
            settings.reporting_api_run_start_endpoint,
        )
                                         or settings.reporting_api_run_start_endpoint,
        reporting_api_test_result_endpoint=env_value(
            "REPORTING_API_TEST_RESULT_ENDPOINT",
            settings.reporting_api_test_result_endpoint,
        )
                                           or settings.reporting_api_test_result_endpoint,
        reporting_api_run_finish_endpoint=env_value(
            "REPORTING_API_RUN_FINISH_ENDPOINT",
            settings.reporting_api_run_finish_endpoint,
        )
                                          or settings.reporting_api_run_finish_endpoint,
        reporting_api_timeout_seconds=int(
            env_value("REPORTING_API_TIMEOUT_SECONDS", str(settings.reporting_api_timeout_seconds))
            or str(settings.reporting_api_timeout_seconds)
        ),
        reporting_api_retries=int(
            env_value("REPORTING_API_RETRIES", str(settings.reporting_api_retries))
            or str(settings.reporting_api_retries)
        ),
        artifacts_dir=env_value("ARTIFACTS_DIR", "artifacts") or "artifacts",
        highlight_on_fail=_as_bool(env_value("HIGHLIGHT_ON_FAIL"), True),
        min_expected_tests=int(env_value("MIN_EXPECTED_TESTS", "1") or "1"),
        visual_enabled=_as_bool(
            env_value("VISUAL_ENABLED"),
            bool(getattr(settings, "visual_enabled", getattr(settings, "visual_enabled", False))),
        ),
        visual_compare_mode=(
                env_value(
                    "VISUAL_COMPARE_MODE",
                    str(getattr(settings, "visual_compare_mode", getattr(settings, "visual_compare_mode", "hybrid"))),
                )
                or "hybrid"
        )
        .strip()
        .lower(),
        visual_baseline_provider=(
                env_value(
                    "VISUAL_BASELINE_PROVIDER",
                    str(
                        getattr(
                            settings, "visual_baseline_provider", getattr(settings, "visual_baseline_provider", "minio")
                        )
                    ),
                )
                or "minio"
        )
        .strip()
        .lower(),
        visual_baseline_profile=env_value(
            "VISUAL_BASELINE_PROFILE",
            str(
                getattr(
                    settings, "visual_baseline_profile", getattr(settings, "visual_baseline_profile", "test-ref")
                )
            ),
        )
                                or "test-ref",
        visual_baseline_version=env_value(
            "VISUAL_BASELINE_VERSION",
            str(
                getattr(settings, "visual_baseline_version", getattr(settings, "visual_baseline_version", "latest"))
            ),
        )
                                or "latest",
        visual_cache_dir=env_value(
            "VISUAL_CACHE_DIR",
            str(getattr(settings, "visual_cache_dir", getattr(settings, "visual_cache_dir", ".visual_cache"))),
        )
                         or ".visual_cache",
        visual_fail_on_missing_baseline=_as_bool(
            env_value("VISUAL_FAIL_ON_MISSING_BASELINE"),
            bool(
                getattr(
                    settings,
                    "visual_fail_on_missing_baseline",
                    getattr(settings, "visual_fail_on_missing_baseline", False),
                )
            ),
        ),
        visual_warn_as_fail=_as_bool(
            env_value("VISUAL_WARN_AS_FAIL"),
            bool(getattr(settings, "visual_warn_as_fail", getattr(settings, "visual_warn_as_fail", False))),
        ),
        visual_minio_endpoint=env_value(
            "VISUAL_MINIO_ENDPOINT",
            str(getattr(settings, "visual_minio_endpoint", getattr(settings, "visual_minio_endpoint", ""))),
        )
                              or "",
        visual_minio_access_key=env_value(
            "VISUAL_MINIO_ACCESS_KEY",
            str(getattr(settings, "visual_minio_access_key", getattr(settings, "visual_minio_access_key", ""))),
        )
                                or "",
        visual_minio_secret_key=env_value(
            "VISUAL_MINIO_SECRET_KEY",
            str(getattr(settings, "visual_minio_secret_key", getattr(settings, "visual_minio_secret_key", ""))),
        )
                                or "",
        visual_minio_bucket=env_value(
            "VISUAL_MINIO_BUCKET",
            str(
                getattr(
                    settings, "visual_minio_bucket", getattr(settings, "visual_minio_bucket", "visual-baselines")
                )
            ),
        )
                            or "visual-baselines",
        visual_minio_secure=_as_bool(
            env_value("VISUAL_MINIO_SECURE"),
            bool(getattr(settings, "visual_minio_secure", getattr(settings, "visual_minio_secure", True))),
        ),
        visual_perceptual_enabled=_as_bool(
            env_value("VISUAL_PERCEPTUAL_ENABLED"),
            bool(
                getattr(
                    settings,
                    "visual_perceptual_enabled",
                    getattr(settings, "visual_perceptual_enabled", False),
                )
            ),
        ),
        visual_perceptual_required=_as_bool(
            env_value("VISUAL_PERCEPTUAL_REQUIRED"),
            bool(
                getattr(
                    settings,
                    "visual_perceptual_required",
                    getattr(settings, "visual_perceptual_required", False),
                )
            ),
        ),
        visual_perceptual_api_url=env_value(
            "VISUAL_PERCEPTUAL_API_URL",
            str(getattr(settings, "visual_perceptual_api_url", getattr(settings, "visual_perceptual_api_url", ""))),
        )
                                  or "",
        visual_perceptual_timeout_seconds=int(
            env_value(
                "VISUAL_PERCEPTUAL_TIMEOUT_SECONDS",
                str(
                    getattr(
                        settings,
                        "visual_perceptual_timeout_seconds",
                        getattr(settings, "visual_perceptual_timeout_seconds", 15),
                    )
                ),
            )
            or "15"
        ),
        visual_perceptual_health_timeout_seconds=int(
            env_value(
                "VISUAL_PERCEPTUAL_HEALTH_TIMEOUT_SECONDS",
                str(
                    getattr(
                        settings,
                        "visual_perceptual_health_timeout_seconds",
                        getattr(settings, "visual_perceptual_health_timeout_seconds", 2),
                    )
                ),
            )
            or "2"
        ),
        visual_perceptual_retries=int(
            env_value(
                "VISUAL_PERCEPTUAL_RETRIES",
                str(
                    getattr(
                        settings,
                        "visual_perceptual_retries",
                        getattr(settings, "visual_perceptual_retries", 2),
                    )
                ),
            )
            or "2"
        ),
        visual_perceptual_fail_fast_errors=int(
            env_value(
                "VISUAL_PERCEPTUAL_FAIL_FAST_ERRORS",
                str(
                    getattr(
                        settings,
                        "visual_perceptual_fail_fast_errors",
                        getattr(settings, "visual_perceptual_fail_fast_errors", 3),
                    )
                ),
            )
            or "3"
        ),
        visual_perceptual_fallback_mode=(
                env_value(
                    "VISUAL_PERCEPTUAL_FALLBACK_MODE",
                    str(
                        getattr(
                            settings,
                            "visual_perceptual_fallback_mode",
                            getattr(settings, "visual_perceptual_fallback_mode", "pixel"),
                        )
                    ),
                )
                or "pixel"
        )
        .strip()
        .lower(),
        visual_perceptual_force_device=(
                env_value(
                    "VISUAL_PERCEPTUAL_FORCE_DEVICE",
                    str(
                        getattr(
                            settings,
                            "visual_perceptual_force_device",
                            getattr(settings, "visual_perceptual_force_device", ""),
                        )
                    ),
                )
                or ""
        )
        .strip()
        .lower(),
        visual_perceptual_max_side=int(
            env_value(
                "VISUAL_PERCEPTUAL_MAX_SIDE",
                str(
                    getattr(
                        settings,
                        "visual_perceptual_max_side",
                        getattr(settings, "visual_perceptual_max_side", 1024),
                    )
                ),
            )
            or "1024"
        ),
        visual_perceptual_overlay_on=(
                env_value(
                    "VISUAL_PERCEPTUAL_OVERLAY_ON",
                    str(
                        getattr(
                            settings,
                            "visual_perceptual_overlay_on",
                            getattr(settings, "visual_perceptual_overlay_on", "test"),
                        )
                    ),
                )
                or "test"
        )
        .strip()
        .lower(),
        visual_perceptual_alpha=float(
            env_value(
                "VISUAL_PERCEPTUAL_ALPHA",
                str(
                    getattr(
                        settings,
                        "visual_perceptual_alpha",
                        getattr(settings, "visual_perceptual_alpha", 0.45),
                    )
                ),
            )
            or "0.45"
        ),
        visual_perceptual_lpips_net=(
                env_value(
                    "VISUAL_PERCEPTUAL_LPIPS_NET",
                    str(
                        getattr(
                            settings,
                            "visual_perceptual_lpips_net",
                            getattr(settings, "visual_perceptual_lpips_net", "vgg"),
                        )
                    ),
                )
                or "vgg"
        )
        .strip()
        .lower(),
    )
