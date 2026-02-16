# netQArner Framework Development Guide

This guide is for maintainers and contributors who develop the `netQArner` test framework.

For day-to-day test execution, use `README.md`.

## Repository layout

- `qa/` - active tests (E2E + API + visual)
- `framework/` - runtime utilities (env, artifacts, logger, reporting, visual runner)
- `tools/` - helper scripts grouped by domain
- `aQuArius/` - central aggregation handoff documentation (separate system)
- `legacy/` - archived old implementation
- `PLAYWRIGHT_BIG_BANG_PLAN.md` - migration plan and progress checklist

## Docs index

- `docs/ARTIFACTS.md`
- `docs/FIXTURES.md`
- `docs/SCENARIO_MODEL.md`
- `docs/REPORTING_HTTP_INTEGRATION.md`
- `tools/README.md`
- `aQuArius/README.md`
- `aQuArius/EVENT_CONTRACT_V2.md`
- `aQuArius/CURRENT_PAYLOAD_AUDIT.md`

## Core commands

```bash
python -m pytest --collect-only -q
python framework/pytest_discovery_guard.py

make validate-config
make test-aso
make test-functional
make test-visual
make clean-artifacts-older DAYS=14

make lint
make format-check
make typecheck
make security
make check
```

## Config validation flow

- `make validate-config` runs:
  - `python tools/scenarios/verify_scenarios.py`
  - `python tools/visual/validate_scenarios.py`
- `make test-aso` runs `validate-config` first, then `pytest -m aso -q`.

## Visual regression development

Visual suites:
- `qa/visual/netcorner/nuxt/pl/hero_page/`
- `qa/visual/netcorner/nuxt/pl/layers/`
- `qa/visual/netcorner/nuxt/pl/product_page/`

Naming and validation rules:
- `qa/visual/validation_rules.json`
- `tools/visual/validate_scenarios.py`

Helpful commands:

```bash
make visual-validate
make test-visual
make visual-approve
make visual-sync
```

Artifact cleanup commands:

```bash
make clean-artifacts
make clean-artifacts-older DAYS=14
```

Local MinIO baseline storage:

```bash
make minio-up
make minio-down
```

## Reporting and local API harness

- Local receiver: `python tools/reporting/test_api.py`
- Make target: `make test-api`
- Contract diagnostics endpoint: `GET /captured/summary`

## Remote/grid helpers

```bash
make remote-up
make remote-smoke
make remote-down
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
- Target routing: `BASE_URL`, `BASE_URL_OVERRIDE`, `server_type`, `server_name`
- Reporting v2: `REPORTING_*`, `FRAMEWORK_VERSION`
- Visual baseline and perceptual: `VISUAL_*`, `VISUAL_MINIO_*`, `VISUAL_PERCEPTUAL_*`
