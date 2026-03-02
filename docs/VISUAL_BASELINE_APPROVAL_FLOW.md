# Visual Baseline Approval Flow

This document describes the local baseline approval workflow driven by the visual report UI.

## Goal

- Mark selected visual results in report as `BASELINE`.
- Confirm write with a human challenge phrase (captcha-like prompt).
- Copy only `TEST` screenshots (`actual_path`) into local baseline storage.
- Keep provider sync (MinIO or other) as a separate step/script.

## How it works

1. Visual tests generate report in `artifacts/<run_id>/visual/`.
2. A local report server is started (`python -m framework.visual.report_server`).
3. User opens report and marks desired rows with `BASELINE`.
4. User clicks `SEND BASELINE` in report header.
5. UI asks backend for challenge phrase and requires manual rewrite.
6. Backend validates challenge and copies selected `actual_path` PNG files to local baseline.

Local baseline destination for `SEND BASELINE` uses a dedicated candidates lane:

`qa/visual/baselines/<suite>/<profile>/candidates/<scenario>__<viewport>__<browser>.png`

Regular baseline resolution for visual compare stays on configured version
(`VISUAL_BASELINE_VERSION`, typically `latest`).

At the same time cache is mirrored into:

`<repo_root>/<VISUAL_CACHE_DIR>/<suite>/<profile>/candidates/...`

## Runbook

1. Generate visual results:

```bash
make test-visual
```

2. Start report server for latest run:

```bash
make report-serve
```

Optional: explicit run id or report path:

```bash
make report-serve RUN_ID=20260218_120000_000001
make report-serve REPORT_DIR=artifacts/20260218_120000_000001/visual PORT=4180
```

3. Open hero page (default: `http://127.0.0.1:4173/`) and select report run.
4. Tag rows with `BASELINE` in viewer.
5. Click `SEND BASELINE`, rewrite shown phrase, confirm.
6. Verify files in `qa/visual/baselines/`.

## API endpoints exposed by report server

- `GET /api/reports` - list visual report runs detected under `artifacts/*/visual`.
- `GET /api/reports/<run_id>/results` - returns report rows.
- `GET /api/reports/<run_id>/image/ref?...` - serves REF image from baseline storage.
- `PUT /reports/<run_id>/vrt-tags.json` - persists tag snapshot for selected run.
- `POST /api/reports/<run_id>/baseline/challenge` - returns one-time phrase + TTL.
- `POST /api/reports/<run_id>/baseline/send` - validates phrase and stores selected local baselines.

`/api/reports/<run_id>/baseline/send` accepts items with:

- `scenario_id`
- `suite_id`
- `viewport`
- `browser`
- `actual_path` (must point to `.png` inside current report dir)

## Safety rules

- Server binds to localhost by default (`127.0.0.1`).
- `actual_path` must resolve inside current report directory.
- Only existing `.png` files are accepted.
- `REF`, `DIFF`, `LPIPS` artifacts are never written as baseline source.

## Future extension: provider sync (MinIO)

Current flow intentionally stops at local baseline write. Provider sync should stay explicit and auditable.

Recommended next step:

1. Add script that uploads from local baseline tree to provider.
2. Optionally expose that script through report server endpoint (whitelisted action only).
3. Keep challenge/confirmation for destructive bulk operations.
4. Record audit log entry with operator, timestamp, run id, and file list.
