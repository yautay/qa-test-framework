# Console log level for Loguru output in new framework.
# Allowed values: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
console_log_level = "WARNING"
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

# Perceptual Metrics Service (PMS) post-process.
pms_enabled = False
pms_required = False
pms_base_url = ""
pms_metric = "both"  # lpips|dists|both
pms_model = "alex"
pms_normalize = False
pms_submit_rps = 2.0
pms_poll_rps = 4.0
pms_max_inflight = 10
pms_server_active_limit = 100
pms_timeout_sec = 60
pms_retry_max = 3
pms_health_timeout_seconds = 2
pms_poll_interval_ms = 500

# Reporting API (optional)
reporting_enabled = False
reporting_schema_version = "2.0"
reporting_source_project = "netQArner"
reporting_source_origin = ""
framework_version = "1.0.0"
reporting_api_url = "http://127.0.0.1:3001"
reporting_api_token = ""
reporting_api_run_start_endpoint = "/test-run/start"
reporting_api_test_result_endpoint = "/test-run/test-result"
reporting_api_run_finish_endpoint = "/test-run/finish"
reporting_api_bug_endpoint = "/test-run/bug-report"
reporting_api_aso_endpoint = "/test-run/aso-report"
reporting_api_note_endpoint = "/test-run/note"
reporting_api_timeout_seconds = 5
reporting_api_retries = 2
