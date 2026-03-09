# Reporting API integration

## Purpose

The framework can report test-run lifecycle and per-test results to external HTTP/HTTPS API endpoints.

Events:
- run start
- test result (per case)
- run finish

## Configuration

Use `.env` (recommended for local setup) or system environment variables.

Supported variables:
- `REPORTING_ENABLED` (`0|1`)
- `REPORTING_SCHEMA_VERSION` (default `2.1`)
- `REPORTING_SOURCE_PROJECT`
- `REPORTING_SOURCE_ORIGIN` (optional override; when empty, framework auto-sets `ci` if `CI` is present, otherwise `local`)
- `REPORTING_SOURCE_PRODUCER_ID` (optional stable producer/agent id, e.g. hostname)
- `REPORTING_API_URL`
- `REPORTING_API_TOKEN` (optional)
- `REPORTING_API_RUN_START_ENDPOINT`
- `REPORTING_API_TEST_RESULT_ENDPOINT`
- `REPORTING_API_RUN_FINISH_ENDPOINT`
- `REPORTING_API_BUG_ENDPOINT`
- `REPORTING_API_ASO_ENDPOINT`
- `REPORTING_API_NOTE_ENDPOINT`
- `REPORTING_API_TIMEOUT_SECONDS`
- `REPORTING_API_RETRIES`

Example:

```env
REPORTING_ENABLED=1
REPORTING_SCHEMA_VERSION=2.1
REPORTING_SOURCE_PROJECT=nc-functional-tests-py
# empty = auto (`ci` when CI env exists, otherwise `local`)
REPORTING_SOURCE_ORIGIN=
# empty = fallback to host name
REPORTING_SOURCE_PRODUCER_ID=
REPORTING_API_URL=http://127.0.0.1:8080
REPORTING_API_TOKEN=
REPORTING_API_RUN_START_ENDPOINT=/test-run/start
REPORTING_API_TEST_RESULT_ENDPOINT=/test-run/test-result
REPORTING_API_RUN_FINISH_ENDPOINT=/test-run/finish
REPORTING_API_BUG_ENDPOINT=/test-run/bug-report
REPORTING_API_ASO_ENDPOINT=/test-run/aso-report
REPORTING_API_NOTE_ENDPOINT=/test-run/note
REPORTING_API_TIMEOUT_SECONDS=5
REPORTING_API_RETRIES=2
```

## URL building

Final URL = `REPORTING_API_URL.rstrip('/') + endpoint`

Example:
- base: `http://127.0.0.1:8080`
- endpoint: `/test-run/start`
- final: `http://127.0.0.1:8080/test-run/start`

## Auth

- If `REPORTING_API_TOKEN` is set, header `Authorization: Bearer <token>` is sent.
- If token is empty, requests are sent without Authorization header.

## Failure behavior

- If `REPORTING_ENABLED=0`, no reporting API calls are made.
- API errors never fail tests.
- Non-2xx or transport errors are logged as warnings.
- Retries and timeout are configurable.

## Payload shape (v2.1)

Every event includes common envelope fields:
- `schema_version`
- `event_id`
- `event_type`
- `event_time_utc`
- `idempotency_key`
- `source` (`project`, `framework_version`, `producer_id`, `instance_id`, `host`, `user`, `worker_id`, `origin`)
- `run_id`
- `run_uid`
- `metadata` (`tester`, `run_note`)

`idempotency_key` is stable per semantic event and uses `run_uid` to avoid collisions in multi-device runs:
- `run_start:{run_uid}:{worker_id}`
- `test_result:{run_uid}:{nodeid}:{attempt}`
- `run_finish:{run_uid}:{worker_id}`

`source.framework_version` is resolved automatically from installed package metadata.
If metadata is unavailable (for example, running from source without installed distribution), value is set to `unknown`.

Run start payload includes:
- `run_started_at`
- `execution` (`browser`, `headless`, `grid_enabled`, `grid_endpoint`, `viewport`, `profile`)
- `target` (`server_name`, `base_url`)
- `git` (`repo`, `commit`, `branch`, `author_name`, `author_email`)

Test result payload includes:
- `test_id`
- `nodeid`
- `status` (`passed|failed|skipped|xfailed|xpassed|error`)
- `attempt`
- `is_flaky`
- `timing` (`started_at`, `finished_at`, `duration_ms`)
- `scenario`
- `markers`
- `artifacts` (trace/video/screenshot metadata list)
- optional `visual`

When `visual` is present, `visual.execution` includes runtime PMS intent fields:
- `pms_requested` (hybrid mode + `PMS_ENABLED=1`)
- `pms_configured` (`PMS_BASE_URL` is not empty)
- `pms_usage_state` (`deferred|disabled|not_applicable`)

On failed tests with screenshot artifacts:
- client sends `multipart/form-data` to test-result endpoint,
- field `payload` contains full JSON payload,
- files are attached as repeated `screenshots` parts (`raw` and `annotated` when available).

If multipart upload fails, client falls back to plain JSON request.

Run finish payload includes:
- `run_finished_at`
- `exit_status`
- `duration_ms`
- `summary` (`total`, `passed`, `failed`, `skipped`, `xfailed`, `xpassed`, `error`)
- `quality_signals` (`retry_count`, `flaky_count`, `slow_regression_count`)

`quality_signals` can additionally include aggregated PMS usage from perceptual postprocess:
- `pms_used`
- `pms_jobs_submitted`
- `pms_jobs_done`
- `pms_jobs_error`
- `pms_jobs_skipped`
- `pms_unavailable_reason`

## Variable precedence

1. system environment variable
2. `.env` file
3. `settings.py` defaults

This allows local `.env` use with easy override in CI.
