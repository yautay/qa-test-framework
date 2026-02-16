# Artifacts Guide

This document explains what is written under `artifacts/<run_id>/` and how to use it.

## Run directory layout

Typical structure:

- `artifacts/<run_id>/logs/`
- `artifacts/<run_id>/screenshots/`
- `artifacts/<run_id>/videos/`
- `artifacts/<run_id>/traces/`
- `artifacts/<run_id>/visual/`
- `artifacts/<run_id>/visual-report/`

## Logs

- `logs/test_run.log` - Loguru output with structured metadata.
- `logs/test_durations.json` - per-test timing snapshot used for trend checks.

## Screenshots

Written mainly on failures:

- raw screenshot (`screenshot_raw`)
- annotated screenshot (`screenshot_annotated`)

Annotated files include metadata overlay to speed up triage.

## Videos

Videos are recorded per context when enabled (`RECORD_VIDEO=1`).
Failure preservation and minimum-duration rules are handled by framework helpers.

## Traces

Tracing starts for E2E contexts and is persisted to `.zip` mainly on failed tests.

Trace zip contains:
- action timeline,
- DOM snapshots,
- network timeline,
- trace screenshots,
- source references.

Open trace locally:

```bash
python -m playwright show-trace artifacts/<run_id>/traces/<file>.zip
```

## Visual artifacts

Visual runs write:

- `visual/actual/` - captured images,
- `visual/diff/` - pixel-diff overlays,
- `visual/heatmap/` - LPIPS heatmaps (when perceptual API is used),
- `visual-report/results.json` - structured result summary,
- `visual-report/index.html` - local interactive report.

## Retention recommendation

Artifacts can grow quickly in long-running environments.
Recommended policy:

- keep recent runs locally,
- archive only needed failures,
- clean old run directories periodically.
