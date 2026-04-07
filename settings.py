# Logging
console_log_level = "WARNING"
console_suppress_reporting_api_logs = True
tools_file_log_level = "WARNING"
tools_logs_dir = "tools/logs"
log_rotation = "50 MB"
log_retention = "7 days"
log_compression = "zip"

# Runtime
artifacts_dir = "artifacts"
ignore_https_errors = True
allure_enabled = False
pytest_html_enabled = True
record_video = True
video_min_seconds = 30
highlight_on_fail = False
min_expected_tests = 1

# Target git-info probe
run_git_info_frontend_url = ""
run_git_info_frontend_endpoint = "/git-info"
run_git_info_backend_url = ""
run_git_info_backend_endpoint = "/git-info"
run_git_info_timeout_seconds = 3

# Grid
grid_provider = "auto"
grid_ws_endpoint = "http://10.21.69.57:4444"
grid_cdp_endpoint = ""
grid_connect_timeout_ms = 30000

# Visual
visual_enabled = True
visual_compare_mode = "hybrid"
visual_baseline_provider = "minio"
visual_baseline_profile = "test-ref"
visual_baseline_version = "latest"
visual_cache_dir = ".visual_cache"
visual_fail_on_missing_baseline = False
visual_freeze_animations = True
visual_shift_compensation_y_px = 100

visual_uncertain_enabled = True
visual_uncertain_pixel_delta = 0.05
visual_uncertain_lpips_delta = 0.05
visual_uncertain_dists_delta = 0.05

visual_viewport_presets = {
    "mobile": (390, 844),
    "tablet": (1024, 1366),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}

# Visual MinIO
visual_minio_endpoint = "s3.cpt-sztos.com"
visual_minio_access_key = "release"
visual_minio_secret_key = "Bytniebytodbyt"
visual_minio_bucket = "visual-baselines"
visual_minio_secure = True

# PMS
pms_enabled = True
pms_base_url = "http://10.21.69.239:8080"
pms_metric = "both"
pms_model = "alex"
pms_normalize = True
pms_submit_rps = 4.0
pms_poll_rps = 4.0
pms_max_inflight = 10
pms_server_active_limit = 40
pms_timeout_sec = 360
pms_retry_max = 3
pms_health_timeout_seconds = 5
pms_poll_interval_ms = 2500
pms_poll_idle_multiplier = 10.0

# Reporting
reporting_enabled = True
reporting_schema_version = "2.1"
reporting_source_project = "netQArner"
reporting_source_producer_id = ""
reporting_api_url = "https://toc-api.cpt-sztos.com"
reporting_api_token = ""
reporting_api_run_start_endpoint = "/test-run/start"
reporting_api_test_result_endpoint = "/test-run/test-result"
reporting_api_run_finish_endpoint = "/test-run/finish"
reporting_api_bug_endpoint = "/test-run/bug-report"
reporting_api_aso_endpoint = "/test-run/aso-report"
reporting_api_log_endpoint = "/test-run/log"
reporting_api_log_level = "INFO"
reporting_api_timeout_seconds = 5
reporting_api_retries = 3
reporting_async_enabled = True
reporting_async_queue_maxsize = 1000
reporting_async_max_attempts = 3
reporting_async_max_retry_age_seconds = 30
reporting_async_flush_timeout_seconds = 3

# Jira
jira_url = "https://jira.netcorner.pl"
jira_username = ""
jira_password = ""
jira_verify_ssl = False
