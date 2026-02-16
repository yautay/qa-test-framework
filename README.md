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
make test-functional
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
- `VISUAL_PERCEPTUAL_ENABLED`, `VISUAL_PERCEPTUAL_REQUIRED`, `VISUAL_PERCEPTUAL_API_URL`

## Visual regression

Visual suites (`qa/visual/netcorner/nuxt/pl`):
- `hero_page/`
- `layers/`
- `product_page/`

Commands:

```bash
make test-visual
make visual-approve
make visual-sync
make minio-up
make minio-down
```

## Artifacts and troubleshooting

- Artifact guide: `docs/ARTIFACTS.md`
- Reporting API details: `docs/REPORTING_HTTP_INTEGRATION.md`
- Local reporting test receiver: `python tools/reporting/test_api.py`

Windows cleanup:
- `tools/windows/Cleanup_Windows.cmd`
- or `powershell -ExecutionPolicy Bypass -File .\tools\windows\cleanup_windows.ps1`

Artifacts cleanup:
- `make clean-artifacts` (remove all local run artifacts)
- `make clean-artifacts-older DAYS=14` (remove run artifacts older than N days)
