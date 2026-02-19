# Console log level for Loguru output in new framework.
# Allowed values: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
console_log_level = "INFO"
ignore_https_errors = True

# General runtime defaults (CI pipelines may override via env)
artifacts_dir = "artifacts"
record_video = True
video_min_seconds = 30
highlight_on_fail = True
min_expected_tests = 1

# Remote Playwright grid compatibility defaults.
grid_ws_endpoint = "ws://127.0.0.1:9323/"
grid_connect_timeout_ms = 30000

# Visual regression defaults.
visual_enabled = True
visual_compare_mode = "pixel"  # pixel|perceptual|hybrid
visual_baseline_provider = "local"  # minio|local
visual_baseline_profile = "test-ref"
visual_baseline_version = "latest"
visual_cache_dir = ".visual_cache"
visual_fail_on_missing_baseline = False
visual_warn_as_fail = False

# Uncertain zone - strefa niepewności (score blisko progu)
visual_uncertain_enabled = True
visual_uncertain_pixel_delta = 0.05  # absolutna wartość dodana do progu
visual_uncertain_lpips_delta = 0.05
visual_uncertain_dists_delta = 0.05

# Visual viewport presets (name -> (width, height))
visual_viewport_presets = {
    "mobile": (390, 844),
    "tablet": (1024, 1366),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}

# MinIO baseline storage.
visual_minio_endpoint = ""
visual_minio_access_key = ""
visual_minio_secret_key = ""
visual_minio_bucket = "visual-baselines"
visual_minio_secure = True

# Perceptual API (LPIPS + DISTS).
visual_perceptual_enabled = False
visual_perceptual_required = False
visual_perceptual_api_url = ""
visual_perceptual_timeout_seconds = 15
visual_perceptual_health_timeout_seconds = 2
visual_perceptual_retries = 2
visual_perceptual_fail_fast_errors = 3
visual_perceptual_fallback_mode = "pixel"  # pixel|abort
visual_perceptual_force_device = ""  # cpu|cuda|""
visual_perceptual_max_side = 1024
visual_perceptual_overlay_on = "test"  # test|ref
visual_perceptual_alpha = 0.45
visual_perceptual_lpips_net = "alex"  # vgg|alex|squeeze

# Reporting API (optional)
reporting_enabled = True
reporting_schema_version = "2.0"
reporting_source_project = "netQArner"
reporting_source_origin = ""
framework_version = "1.0.0"
reporting_api_url = ""
reporting_api_token = ""
reporting_api_run_start_endpoint = "/test-run/start"
reporting_api_test_result_endpoint = "/test-run/test-result"
reporting_api_run_finish_endpoint = "/test-run/finish"
reporting_api_bug_endpoint = "/test-run/bug-report"
reporting_api_aso_endpoint = "/test-run/aso-report"
reporting_api_timeout_seconds = 5
reporting_api_retries = 2
