## Perceptual Metrics Service Integration

This repository uses a post-process step after visual tests finish (single pytest and pytest-xdist controller) to compute LPIPS/DISTS asynchronously via PMS.

### Flow

1. Visual tests produce `VisualResult` entries (`baseline_path`/`actual_path`).
2. Post-process creates deterministic PMS jobs (`job_id` derived from `run_id + pair_id + metric + model + normalize`).
3. Jobs are submitted to `POST /v1/compare/jobs` with backpressure controls.
4. Job statuses are polled via `GET /v1/compare/jobs/{job_id}`.
5. For completed LPIPS jobs, heatmaps are downloaded from `GET /v1/compare/jobs/{job_id}/heatmap`.
6. `results.json` is updated with:
   - `perceptual.status`
   - `perceptual.lpips`
   - `perceptual.dists`
   - `perceptual.heatmap`
   - `perceptual.job_id`
   - `perceptual.timing_ms`
   - `perceptual.error_message`

Compatibility fields (`lpips`, `dists`, `heatmap_path`) are also populated for existing UI logic.

### Environment variables

- `PMS_ENABLED`
- `PMS_BASE_URL`
- `PMS_METRIC` (`lpips|dists|both`)
- `PMS_MODEL` (default `alex`)
- `PMS_NORMALIZE` (`0|1`)
- `PMS_SUBMIT_RPS`
- `PMS_POLL_RPS`
- `PMS_MAX_INFLIGHT`
- `PMS_SERVER_ACTIVE_LIMIT`
- `PMS_TIMEOUT_SEC`
- `PMS_RETRY_MAX`
- `PMS_HEALTH_TIMEOUT_SECONDS`
- `PMS_POLL_INTERVAL_MS`

### Backpressure behavior

- Local in-flight jobs are capped by `PMS_MAX_INFLIGHT`.
- Submit and poll rates are throttled independently (`PMS_SUBMIT_RPS`, `PMS_POLL_RPS`).
- Global server pressure is measured with `GET /v1/compare/jobs` (`queued + running`).
- If `server_active >= PMS_SERVER_ACTIVE_LIMIT`, submit is paused while polling continues.

### Logging

Loguru events include structured fields for troubleshooting (`run_id`, `pair_id`, `job_id`, `status`).

- `DEBUG`: queue snapshots, polling transitions, wait states
- `INFO`: lifecycle start/finish, successful submit/done events
- `WARNING`: retry attempts, transient poll/list failures
- `ERROR`: submit failures, timeout, terminal job errors
