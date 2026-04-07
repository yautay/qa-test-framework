# Artifacts Guide

This document explains how runtime artifacts are built and finalized under `artifacts/<run_id>/`.

## Directory layout

Typical structure for one run:

- `artifacts/<run_id>/logs/`
- `artifacts/<run_id>/screenshots/`
- `artifacts/<run_id>/videos/`
- `artifacts/<run_id>/traces/`
- `artifacts/<run_id>/visual/`
- `artifacts/<run_id>/workers/` (xdist only)

## Run id and run root

Run root is resolved in `qa/conftest.py` via `resolve_artifacts_base_dir(...)` and `build_run_artifacts(...)`.

- Non-xdist run: run id is timestamp (`YYYYMMDD_HHMMSS_microseconds`).
- Xdist controller: run id is initialized once and shared with workers.
- Xdist worker: run id is read from `workerinput["run_id"]`.

Important behavior:

- Worker must receive `run_id` from controller; otherwise startup fails fast.
- This guarantees one shared run directory for all workers.

## What writes artifacts

Core run directories are created by `framework/artifacts.py`:

- `logs/`
- `screenshots/`
- `videos/`
- `traces/`

Per-test writing:

- screenshots, traces, videos are written by test/runtime helpers during test execution,
- filenames are already worker-safe (unique test/node id based naming).

Run-level writing:

- `run-metadata.json` is written early in `qa/conftest.py` (tester + run_note),
- `logs/test_durations_<worker>.json` is written by each worker,
- `logs/test_durations.json` is merged on xdist controller at session finish.

### run-metadata target git info

`run-metadata.json` includes run-level git info for target applications under:

- `target_git_info.frontend`
- `target_git_info.backend`

Each target entry is normalized to:

- `branch` (string)
- `commit` (string)
- `endpoint` (string)
- `url` (string)
- `status` (`ok`, `error`, `invalid_payload`, `not_configured`)
- `error` (string)
- `fetched_at_utc` (UTC timestamp)

Behavior guarantees:

- probe is executed once per run (not per test),
- probe failures never fail the test session,
- failures are logged as `WARNING`,
- payload is persisted even on error, so downstream reporting/UI keeps a stable shape,
- URL resolution is aligned with `environment_probe` refresh (if `base_url` is unknown at startup, git-info is refreshed later when target URL is resolved).

Notes:

- endpoint can be relative (joined with resolved target `base_url`) or absolute (`https://...`),
- when multiple target base URLs are detected in one run, the first sorted URL is used and a warning is logged,
- accepted payload keys include `branch`/`branchName` and `commit`/`commit_hash`/`commitHash`.

Config knobs (`settings.py` / env):

- `run_git_info_frontend_endpoint` / `RUN_GIT_INFO_FRONTEND_ENDPOINT`
- `run_git_info_backend_endpoint` / `RUN_GIT_INFO_BACKEND_ENDPOINT`
- `run_git_info_timeout_seconds` / `RUN_GIT_INFO_TIMEOUT_SECONDS`

## Visual flow (single process)

Without xdist:

- tests append `VisualResult` objects to session fixture list,
- fixture finalizer calls `write_visual_report(...)`,
- report outputs are generated directly in `visual/`.

## Visual flow (xdist)

With xdist:

1. Worker phase:
   - each worker writes `workers/<gw>/visual_results.json` at session end,
   - each worker writes `logs/test_durations_<gw>.json`.

2. Controller phase:
   - plugin `framework/plugins/xdist_report_finalize.py` runs on controller,
   - worker `visual_results.json` files are loaded and merged,
   - merge key is `(scenario_id, viewport, browser)` (last write wins),
   - `write_visual_report(...)` is called once,
   - durations are merged into `logs/test_durations.json`.

## Visual report outputs

`framework/visual/report_builder.py` generates:

- `visual/results.json` - machine-readable result list,
- `visual/index.html` - offline report page,
- `visual/assets/*` - bundled frontend assets,
- `visual/vrt-tags.json` - tags snapshot file,
- `visual/.report-ready.json` - readiness marker for report discovery.

`actual/` and `diff/` are produced by visual runner execution. PMS post-process writes LPIPS heatmaps into `visual/heatmaps/` and updates `results.json` (`perceptual.*` + compatibility `lpips/dists/heatmap_path`).

## Asset copy behavior

Assets are copied file-by-file (not metadata-preserving copy). This avoids cross-platform permission issues seen on Windows/WSL/NFS setups.

## Logs

- `logs/run_<run_id>_<worker>.log` - structured Loguru JSON logs (per worker + controller file),
- `logs/test_durations_<worker>.json` - worker-local timing snapshots,
- `logs/test_durations.json` - merged timing snapshot.

## Troubleshooting checklist

If visual report files are missing:

1. Check `workers/*/visual_results.json` exists.
2. Check controller log for `visual_worker_results_missing`.
3. Check controller log for `visual_report_finalize_failed`.
4. Verify `framework/visual/ui/dist/` exists (built frontend bundle).
5. Verify all workers and controller use the same `artifacts/<run_id>/` root.

## Retention recommendation

Artifacts can grow quickly in CI and long-lived environments.

- keep only recent runs locally,
- archive selected failing runs,
- periodically prune old `artifacts/<run_id>/` directories.
