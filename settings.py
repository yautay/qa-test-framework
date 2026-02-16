# Console log level for Loguru output in new framework.
# Allowed values: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
console_log_level = "ERROR"

# Remote Playwright grid compatibility defaults.
is_grid_available = False
grid_ws_endpoint = "ws://127.0.0.1:9323/"
grid_connect_timeout_ms = 30000

# Visual regression defaults.
visual_enabled = True
visual_compare_mode = "hybrid"  # pixel|perceptual|hybrid
visual_baseline_provider = "minio"  # minio|local
visual_baseline_profile = "test-ref"
visual_baseline_version = "latest"
visual_cache_dir = ".visual_cache"
visual_fail_on_missing_baseline = False
visual_warn_as_fail = False

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
visual_perceptual_lpips_net = "vgg"  # vgg|alex|squeeze
