# netQArner Framework Development Guide

This guide is for maintainers and contributors who develop the `netQArner` test framework.

For day-to-day test execution, use `README.md`.

## Repository layout

- `qa/` - active tests (E2E + API + visual)
- `framework/` - runtime utilities (env, artifacts, logger, reporting, visual runner)
- `tools/` - helper scripts grouped by domain

## Development environment (WSL2)

- Recommended model on Windows: VSCode on host + WSL2 terminal/runtime.
- First-time setup in WSL: `bash tools/wsl/Setup_WSL.sh`
- Health check: `bash tools/wsl/run.sh doctor`
- After `git pull`: `bash tools/wsl/run.sh sync`
- `make` targets now prefer `.venv/bin/python` when available, which prevents Python version drift.

## Docs index

- `docs/ARTIFACTS.md`
- `docs/E2E_PAGE_OBJECT_CONTRACT.md`
- `docs/FIXTURES.md`
- `docs/PAGE_OBJECTS_EN.md`
- `docs/PAGE_OBJECTS_PL.md`
- `docs/REPORTING_HTTP_INTEGRATION.md`
- `docs/VISUAL_BASELINE_APPROVAL_FLOW.md`

## Core commands

```bash
uv python install 3.13.2
uv sync --frozen --extra dev

uv run --frozen --extra dev python -m pytest --collect-only -q
uv run --frozen --extra dev python framework/pytest_discovery_guard.py

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

## VSCode test debugging

Repository-tracked debug profiles live in `.vscode/launch.json`.

- `Pytest: Debug Test (breakpoint-friendly)` is the default for Test Explorer (`purpose: ["debug-test"]`).
- `Pytest: Debug Test (framework step-in)` is for manual launch when stepping through framework/fixture internals.

Both profiles keep local debugging responsive by disabling heavy extras:

- `REPORTING_ENABLED=0`
- `ALLURE_ENABLED=0`
- `PYTEST_HTML_ENABLED=0`
- `RECORD_VIDEO=0`
- `VISUAL_ENABLED=0`
- `PMS_ENABLED=0`

Notes:

- Target routing still comes from runtime defaults (`settings_cli.py`) unless you pass `--server-name` manually.
- A short `about:blank` tab is expected: Playwright page is created before first test navigation.
- For stable breakpoints, stop after first `open()/goto()` call, not before it.
- After pulling launch config changes, run `Developer: Reload Window` in VSCode.

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

Note: project runtime targets Python `3.13.2` (`.python-version`, `uv.lock`), so run backend tests on Python `3.13.2`.

## Report UI runtime

- Testers use committed `framework/visual/ui/dist/`, so local report server works without Node.
- Only maintainers of `framework/visual/ui` need Node `22` (`framework/visual/ui/.nvmrc`).
- After UI changes, run `npm ci`, `npm run test:unit`, `npm run build:fast`, then commit updated `dist/`.

Reference: `docs/VISUAL_BASELINE_APPROVAL_FLOW.md`

Visual baseline promotion/versioning scripts: `tools/visual/README.md`
Operator runbook: `tools/visual/OPERATOR_RUNBOOK.md`

Examples:

```bash
python tools/visual/promote_candidates_local.py --apply
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1 --apply
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --with-minio --apply
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --with-minio --apply --ask-release-credentials
python tools/visual/retention_baselines.py --with-minio --apply --ask-release-credentials
```

Scenario JSON reference and authoring guide: `qa/visual/README.md`

Artifact cleanup commands:

```bash
make clean
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

## Jira visual reporting flow

- Enable Jira integration by configuring `JIRA_ENABLED=1`, `JIRA_URL`, and either credentials (`JIRA_USERNAME`+`JIRA_PASSWORD`) or `JIRA_AUTH_MODE=token` with `JIRA_API_TOKEN`.
- Set optional `JIRA_ASO_MENTIONS` to `[~username]` tokens demarking ASO owners who should be mentioned in comments.
- Run `make report-serve`, open the hero page, and click the new envelope action available once PMS is finished; fill in the Jira ticket, optional note, and credentials when prompted.
- Use `npm run test:unit` (in `framework/visual/ui`) to cover the UI modal and API wrapper, and `python -m pytest qa/aso/framework/visual/test_report_server_http_jira.py -q` to exercise the new backend route.

## Remote/grid helpers

```bash
make debug-remote-grid-up
make debug-remote-grid-down
```

## Environment matrix (developer view)

Main defaults:
- `settings_cli.py`
- fallback compatibility defaults: `settings.py`
- optional overrides: `.env`

Important env groups:
- Runtime/browser/grid: `BROWSER`, `HEADLESS`, `IS_GRID_AVAILABLE`, `GRID_*`
- Target routing: `BASE_URL`, `BASE_URL_OVERRIDE`, `REFERENCE_HOST` + CLI `--server-name`
- Reporting v2: `REPORTING_*`
- Visual baseline and perceptual post-process: `VISUAL_*`, `VISUAL_MINIO_*`, `PMS_*`

Target routing migration (hard cut):
- Removed: `--server-type` and `settings_cli.server_type`.
- New model: only `--server-name` (or `settings_cli.server_name`) selects target.
- Accepted `--server-name` values:
  - `demo`, `prod`, `local` (fixed environment aliases),
  - DNS host token (e.g. `weryfikacja.alfa`) for test template URLs.
- `REFERENCE_HOST` keeps the same selector logic (`demo`/`prod`/`local` or DNS token).

Examples:

```bash
# old (removed)
pytest --server-type test --server-name weryfikacja.alfa

# new
pytest --server-name weryfikacja.alfa
pytest --server-name demo
```

Reporting notes:
- `REPORTING_SOURCE_ORIGIN` can be left empty to auto-detect (`ci` when `CI` exists, otherwise `local`).
- `source.framework_version` is auto-resolved from package metadata (falls back to `unknown` when metadata is unavailable).

#### Grid Authentication

| Env var | Description |
|---|---|
| `GRID_WS_AUTH_MODE` | Auth mode for the WS endpoint and all Selenium HTTP probes: `none` (default), `basic`, or `token` |
| `GRID_WS_USERNAME` | Username for `basic` mode |
| `GRID_WS_PASSWORD` | Password for `basic` mode |
| `GRID_WS_TOKEN` | Bearer token for `token` mode |

Examples:

```bash
# Basic auth on the WS/HTTP Grid endpoint
GRID_WS_AUTH_MODE=basic
GRID_WS_USERNAME=user
GRID_WS_PASSWORD=secret

# Bearer token on the WS/HTTP Grid endpoint
GRID_WS_AUTH_MODE=token
GRID_WS_TOKEN=mytoken
```

> Note: `GRID_WS_AUTH_MODE` credentials are applied to the Playwright WebSocket connect call.
