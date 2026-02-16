# Runtime settings for local test execution.
# Values can be overridden by environment variables.

# Legacy compatibility
is_grid_available = False
grid_ws_endpoint = "ws://127.0.0.1:9323/"
grid_connect_timeout_ms = 30000
is_session_headless = True
ignore_https_errors = True
console_log_level = "ERROR"

# Browser runtime
# Supported: chromium, firefox, webkit, chrome
browser = "chromium"

# Supported: test, demo, prod, local
# Suite URL mapping uses this value directly (no env override).
server_type = "test"

# Example legacy-compatible server name: "koncerz.test"
# Suite URL mapping uses this value directly (no env override).
server_name = "koncerz.test"
server_ssh_port = "56855"

# Legacy compatibility contacts
email_for_production_tests = "kolorowy@test.pl"
phone_for_production_tests = "123123123"

# Optional direct URL override; if set, this wins over generated values.
base_url_override = ""

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
reporting_api_timeout_seconds = 5
reporting_api_retries = 2

# Visual regression
visual_enabled = False
visual_compare_mode = "hybrid"  # pixel|perceptual|hybrid
visual_baseline_provider = "minio"  # minio|local
visual_baseline_profile = "test-ref"
visual_baseline_version = "latest"
visual_cache_dir = ".visual_cache"
visual_fail_on_missing_baseline = False
visual_warn_as_fail = False

# MinIO baseline storage
visual_minio_endpoint = ""
visual_minio_access_key = ""
visual_minio_secret_key = ""
visual_minio_bucket = "visual-baselines"
visual_minio_secure = True

# Perceptual API
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
visual_perceptual_lpips_net = "vgg"  # vgg|alex|squeeze
