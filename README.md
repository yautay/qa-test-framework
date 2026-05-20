# netQArner Test Framework

`netQArner` is the QA test framework used to run E2E, API, and visual regression tests.

If you develop the framework itself, use `README-DEV.md`.

## CI status

### CI Actions

| Job | develop | netquarner |
| --- | --- | --- |
| Lint/Format/Typecheck | [![Lint develop](https://github.com/yautay/qa-test-framework/actions/workflows/ci-lint.yml/badge.svg?branch=develop)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-lint.yml?query=branch%3Adevelop) | [![Lint netquarner](https://github.com/yautay/qa-test-framework/actions/workflows/ci-lint.yml/badge.svg?branch=netquarner)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-lint.yml?query=branch%3Anetquarner) |
| Security | [![Security develop](https://github.com/yautay/qa-test-framework/actions/workflows/ci-security.yml/badge.svg?branch=develop)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-security.yml?query=branch%3Adevelop) | [![Security netquarner](https://github.com/yautay/qa-test-framework/actions/workflows/ci-security.yml/badge.svg?branch=netquarner)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-security.yml?query=branch%3Anetquarner) |
| ASO tests | [![ASO develop](https://github.com/yautay/qa-test-framework/actions/workflows/ci-aso.yml/badge.svg?branch=develop)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-aso.yml?query=branch%3Adevelop) | [![ASO netquarner](https://github.com/yautay/qa-test-framework/actions/workflows/ci-aso.yml/badge.svg?branch=netquarner)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-aso.yml?query=branch%3Anetquarner) |
| Frontend UI | [![Frontend develop](https://github.com/yautay/qa-test-framework/actions/workflows/ci-frontend.yml/badge.svg?branch=develop)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-frontend.yml?query=branch%3Adevelop) | [![Frontend netquarner](https://github.com/yautay/qa-test-framework/actions/workflows/ci-frontend.yml/badge.svg?branch=netquarner)](https://github.com/yautay/qa-test-framework/actions/workflows/ci-frontend.yml?query=branch%3Anetquarner) |

### GitLab, Bitbucket, Jenkins

CI configs are included in this repository (`.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile`).
If your GitLab/Bitbucket/Jenkins instances expose public badge URLs, add them here using each platform-specific badge endpoint.

## Quick start

### Windows (recommended)

Detailed step-by-step guide for testers: `docs/WINDOWS_SETUP_DLA_TESTERA.md`
English version: `docs/WINDOWS_SETUP_FOR_TESTER.md`

Option A (double-click):
1. Open the `tools/windows` folder.
2. Run `Setup_Windows.cmd`.
3. Wait for bootstrap to finish (`uv`, Python `3.13.2`, `.venv`, dependencies, Playwright Chromium).

Option B (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

Recommended post-check:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 doctor
```

Daily Windows commands:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 aso
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 e2e
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 report
```

Node is not required for testers on Windows. The report app uses committed `framework/visual/ui/dist/`.
Node `22` is only needed when maintaining the report UI itself.

### Linux/macOS (WSL2 recommended on Windows)

Option A (WSL helper script):

```bash
bash tools/wsl/Setup_WSL.sh
```

Recommended post-check:

```bash
bash tools/wsl/run.sh doctor
```

Option B (manual):

```bash
uv python install 3.13.2
uv sync --frozen --extra dev
uv run --frozen --extra dev python -m playwright install chromium
```

## Run tests

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 api
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 aso
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 e2e
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 verify
```

### Linux/macOS

```bash
make test-e2e
make test-visual
make test-aso
make clean-artifacts-older DAYS=14
```

WSL wrapper commands (optional):

```bash
bash tools/wsl/run.sh aso
bash tools/wsl/run.sh e2e
bash tools/wsl/run.sh visual
bash tools/wsl/run.sh report
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
- `server_name` (in `settings_cli.py`)
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

Windows equivalents:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 report
docker compose -f tools\minio\docker-compose.yml up -d
docker compose -f tools\minio\docker-compose.yml down
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
Visual JSON full template guide (layers): `qa/visual/docs/README.md`

## Artifacts and troubleshooting

- Artifact guide: `docs/ARTIFACTS.md`
- Reporting API details: `docs/REPORTING_HTTP_INTEGRATION.md`
- Allure / pytest-html metadata include run-level target git fields (`target_git_frontend_*`, `target_git_backend_*`)

Windows cleanup:
- `tools/windows/Cleanup_Windows.cmd`
- or `powershell -ExecutionPolicy Bypass -File .\tools\windows\cleanup_windows.ps1`

Artifacts cleanup:
- `make clean` (full local cleanup: run artifacts + tools logs + common caches)
- `make clean-artifacts` (same as `make clean`)
- `make clean-artifacts-older DAYS=14` (remove run artifacts older than N days)
