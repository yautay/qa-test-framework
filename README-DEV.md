# netQArner Framework Development Guide

This guide is for maintainers and contributors who develop the `netQArner` test framework.

For day-to-day test execution, use `README.md`.

## Repository layout

- `qa/` - active tests (E2E + API + visual)
- `framework/` - runtime utilities (env, artifacts, logger, reporting, visual runner)
- `tools/` - helper scripts grouped by domain

## Docs index

- `docs/ARTIFACTS.md`
- `docs/FIXTURES.md`
- `docs/SCENARIO_MODEL.md`
- `docs/REPORTING_HTTP_INTEGRATION.md`
- `docs/visual-timeout-postmortem.md`
- `tools/README.md`

## Core commands

```bash
python -m pytest --collect-only -q
python framework/pytest_discovery_guard.py

make test-aso
make test-e2e
make test-visual
make clean-artifacts-older DAYS=14

make lint
make format-check
make typecheck
make security
make check
```

## Config validation flow

- `make verify-scenarios` runs `python tools/scenarios/verify_scenarios.py`
- `make verify-discovery` runs `python framework/pytest_discovery_guard.py`

## Visual regression development

Visual suites:
- `qa/visual/netcorner/nuxt/pl/hero_page/`
- `qa/visual/netcorner/nuxt/pl/layers/`
- `qa/visual/netcorner/nuxt/pl/product_page/`

Helpful commands:

```bash
make test-visual
make report-serve
```

Report-driven local baseline approval:

- run `make report-serve` (optionally `RUN_ID=...`),
- open hero page (`http://127.0.0.1:4173/`) and select run,
- mark rows with `BASELINE`,
- use `SEND BASELINE` + challenge phrase confirmation,
- only `TEST` screenshots are stored as local baselines.

UI unit tests for visual report app (`framework/visual/ui`):

- `npm run test:unit` - run Vitest suite,
- `npm run build` - build bundle and automatically run UI tests after build.

Backend unit tests for report server (kept under `qa/aso/framework/visual/`):

```bash
pytest qa/aso/framework/visual/test_report_server_units.py -q
pytest qa/aso/framework/visual/test_report_server_http_endpoints.py -q
```

Note: project runtime targets Python 3.13 (`pyproject.toml`), so run backend tests on Python 3.13.

Reference: `docs/VISUAL_BASELINE_APPROVAL_FLOW.md`

Visual baseline promotion/versioning scripts: `tools/visual/README.md`

Examples:

```bash
python tools/visual/promote_candidates_local.py --apply
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1 --apply
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --with-minio --apply
```

Scenario JSON reference and authoring guide: `qa/visual/README.md`

Artifact cleanup commands:

```bash
make clean-artifacts
make clean-artifacts-older DAYS=14
```

Local MinIO baseline storage:

```bash
make debug-minio-up
make debug-minio-down
```

## Reporting and local API harness

- Make target: `make test-api`

## Remote/grid helpers

```bash
make debug-remote-grid-up
make debug-remote-grid-down
```

## Local git hooks

- Hook source: `tools/hooks/pre-commit-aso.sh`
- Install: `./tools/hooks/install-local-hooks.sh`
- Hook behavior: runs `make test-aso` before commit

## Environment matrix (developer view)

Main defaults:
- `settings_cli.py`
- fallback compatibility defaults: `settings.py`
- optional overrides: `.env`

Important env groups:
- Runtime/browser/grid: `BROWSER`, `HEADLESS`, `IS_GRID_AVAILABLE`, `GRID_*`
- Target routing: `BASE_URL`, `BASE_URL_OVERRIDE`, `REFERENCE_HOST` + CLI `--server-type`, `--server-name`
- Reporting v2: `REPORTING_*`
- Visual baseline and perceptual post-process: `VISUAL_*`, `VISUAL_MINIO_*`, `PMS_*`

Reporting notes:
- `REPORTING_SOURCE_ORIGIN` can be left empty to auto-detect (`ci` when `CI` exists, otherwise `local`).
- `source.framework_version` is auto-resolved from package metadata (falls back to `unknown` when metadata is unavailable).
