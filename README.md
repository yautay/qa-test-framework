# netQArner Test Framework

`netQArner` is the QA test framework used to run E2E, API, and visual regression tests.

If you develop the framework itself, use `README-DEV.md`.

## Quick start

### Windows (recommended)

Option A (double-click):
1. Open the `tools/windows` folder.
2. Run `Setup_Windows.cmd`.
3. Follow setup prompts.

Option B (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\setup_windows.ps1
```

Activate virtual environment:

```powershell
powershell -ExecutionPolicy Bypass -File .\.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
pyenv install -s 3.13.2
pyenv local 3.13.2
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m playwright install chromium
```

## Run tests

```bash
make test-e2e
make test-visual
make test-aso
make clean-artifacts-older DAYS=14
```

Useful selectors:

```bash
python -m pytest -m smoke -q
python -m pytest -m "e2e and not slow" -q
python -m pytest -m api -q
python -m pytest -m visual -q
```

Viewport options:
- `--viewport mobile|tablet|fhd|2k|4k` (default: `fhd`)
- `--visual-viewports mobile,tablet,fhd` (visual matrix)

## Basic configuration

Main local config: `settings_cli.py`.
Optional overrides: copy `.env.example` to `.env`.

Key values for regular execution:
- `BASE_URL` or `BASE_URL_OVERRIDE`
- `server_type`, `server_name` (in `settings_cli.py`)
- `BROWSER`, `HEADLESS`
- `VISUAL_ENABLED`
- `PMS_ENABLED`, `PMS_BASE_URL` (+ throttling knobs in `.env.example`)

## Visual regression

Visual suites (`qa/visual/netcorner/nuxt/pl`):
- `hero_page/`
- `layers/`
- `product_page/`

Commands:

```bash
make test-visual
make report-serve
make debug-minio-up
make debug-minio-down
```

Baseline review from report UI:

- start report server (`make report-serve`),
- open hero page (`http://127.0.0.1:4173/`) and pick report run,
- tag rows with `BASELINE`,
- click `SEND BASELINE` and rewrite challenge phrase,
- selected `TEST` images are copied to local baseline candidates (`qa/visual/baselines/<suite>/<profile>/candidates`).

Details: `docs/VISUAL_BASELINE_APPROVAL_FLOW.md`

Baseline promotion/versioning scripts: `tools/visual/README.md`
Operator runbook: `tools/visual/OPERATOR_RUNBOOK.md`

Examples:

```bash
python tools/visual/promote_candidates_local.py --apply
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1 --apply
python tools/visual/version_baselines.py list --with-minio
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --with-minio --apply --ask-release-credentials
python tools/visual/retention_baselines.py --with-minio --apply --ask-release-credentials
```

Scenario JSON reference and authoring guide: `qa/visual/README.md`

## Artifacts and troubleshooting

- Artifact guide: `docs/ARTIFACTS.md`
- Reporting API details: `docs/REPORTING_HTTP_INTEGRATION.md`

Windows cleanup:
- `tools/windows/Cleanup_Windows.cmd`
- or `powershell -ExecutionPolicy Bypass -File .\tools\windows\cleanup_windows.ps1`

Artifacts cleanup:
- `make clean-artifacts` (remove all local run artifacts)
- `make clean-artifacts-older DAYS=14` (remove run artifacts older than N days)
