# Event contract v2

This contract is designed for multi-runner aggregation.

## Design principles

- Versioned schema (`schema_version`).
- Event-level idempotency (`idempotency_key`).
- Stable run identity (`run_id`) and runner identity (`instance_id`).
- Full status model for analytics and flaky detection.
- Artifact metadata that can outlive local file paths.

## Common envelope

All events MUST include:

```json
{
  "schema_version": "2.0",
  "event_id": "2fbd6628-12d8-4d2f-aafb-73f981cb4a45",
  "event_type": "run_start",
  "event_time_utc": "2026-02-15T10:00:00.000Z",
  "idempotency_key": "run_start:20260215_100000:master",
  "source": {
    "project": "nc-functional-tests-py",
    "framework_version": "1.0.0",
    "instance_id": "hostA-userB-pid1234",
    "host": "KT-D3115003",
    "user": "tester.name",
    "worker_id": "master",
    "origin": "local"
  }
}
```

`origin` values: `local|ci|server`.

## Event: run_start

Required fields:

- `run_id`
- `run_started_at`
- `execution`
  - `browser`, `headless`, `grid_enabled`, `grid_endpoint`, `viewport`
  - `profile` (`aso|functional|smoke|nightly|release|custom`)
- `target`
  - `server_type`, `server_name`, `base_url`
- `git`
  - `repo`, `branch`, `commit`, `author_name`, `author_email`

Example:

```json
{
  "schema_version": "2.0",
  "event_id": "e50f69df-c512-4d67-b3f4-5a2200a761cb",
  "event_type": "run_start",
  "event_time_utc": "2026-02-15T10:00:00.000Z",
  "idempotency_key": "run_start:20260215_100000:master",
  "source": {
    "project": "nc-functional-tests-py",
    "framework_version": "1.0.0",
    "instance_id": "KT-D3115003-mp-12345",
    "host": "KT-D3115003",
    "user": "michal.pielaszkiewicz",
    "worker_id": "master",
    "origin": "local"
  },
  "run_id": "20260215_100000",
  "run_started_at": "2026-02-15T10:00:00.000Z",
  "execution": {
    "browser": "chromium",
    "headless": true,
    "grid_enabled": false,
    "grid_endpoint": "",
    "viewport": "fhd",
    "profile": "functional"
  },
  "target": {
    "server_type": "test",
    "server_name": "koncerz.test",
    "base_url": "https://komputronik-koncerz.test.netcorner.pl"
  },
  "git": {
    "repo": "github.com:yautay/playwright-migration.git",
    "branch": "refactor/playwright-bigbang-basepage",
    "commit": "abcdef1234567890",
    "author_name": "Michal Pielaszkiewicz",
    "author_email": "michal.pielaszkiewicz@komputronik.pl"
  }
}
```

## Event: test_result

Required fields:

- `run_id`
- `test_id` (stable hash or canonical key)
- `nodeid`
- `status` (`passed|failed|skipped|xfailed|xpassed|error`)
- `attempt` (starts at 1)
- `timing`
  - `started_at`, `finished_at`, `duration_ms`

Optional fields:

- `scenario`
- `markers`
- `is_flaky`
- `error` (`type`, `message`, `stack`, `category`)
- `artifacts` (list)
- `visual` object (for visual regression scenarios):
  - `threshold_scope` (`scenario+viewport+browser`)
  - `thresholds_used`:
    - `pixel_max`
    - `lpips_max`
    - `dists_max`
  - `scores`:
    - `pixel_changed_ratio`
    - `lpips`
    - `dists`
  - `verdict` (`pass|warn|fail`)

Artifact item shape:

- `kind` (`trace|video|screenshot_raw|screenshot_annotated|log|other`)
- `path` (local path, optional)
- `uri` (portable URL, optional)
- `sha256` (optional)
- `size_bytes` (optional)
- `available` (bool)

## Event: run_finish

Required fields:

- `run_id`
- `run_finished_at`
- `exit_status`
- `duration_ms`
- `summary`
  - `total`, `passed`, `failed`, `skipped`, `xfailed`, `xpassed`, `error`

Optional fields:

- `quality_signals`
  - `retry_count`, `flaky_count`, `slow_regression_count`

## Compatibility strategy

- Keep accepting legacy v1 payloads during migration period.
- Runner sends `schema_version=2.0` once central endpoint is ready.
- If central returns `409` for duplicate `idempotency_key`, runner treats as success.

## Visual threshold policy notes

- AQ aggregates and trends visual scores per `scenario_id + viewport + browser_family`.
- AQ MUST NOT split threshold identity by environment.
- AQ recommendations require minimum sample size of 20 runs.
- AQ MUST cap suggested threshold increase to +20% per single update step.
