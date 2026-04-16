# AGENTS.md

## Scope
- Python runtime is 3.13. Use `python -m pip install -e ".[dev]"` for backend/dev dependencies.
- The only separate Node project is `framework/visual/ui` (CI uses Node 22 there). Run `npm ci` inside that directory; the repo root is not a Node workspace.
- `qa/aso/framework/**` is the main framework regression/unit-style suite for `framework/`; most backend tests are there, not under a top-level `tests/` directory.

## Verified Commands
- Root `Makefile` is the source of truth for Python commands. Check `make help` before trusting README command lists.
- Full Python verification is `make check`, in this order: `test-aso -> lint -> format-check -> typecheck -> security -> verify-discovery -> verify-scenarios -> collect`.
- Focused suites: `make test-aso`, `make test-e2e`, `make test-api`, `make test-visual`, `make test-smoke`.
- `make check` does not cover the Vue report UI. If you touch `framework/visual/ui`, also run `npm run test:unit` and `npm run build:fast` in `framework/visual/ui` to match CI.
- `make report-serve` only starts the Python report server. It fails if `framework/visual/ui/dist` is missing; build the UI first with `npm run build` or `npm run build:fast` in `framework/visual/ui`.
- CI ASO parity env: `HEADLESS=1 IS_GRID_AVAILABLE=0 REPORTING_ENABLED=0 ALLURE_ENABLED=0 PYTEST_HTML_ENABLED=0 RECORD_VIDEO=0` before `make verify-discovery`, `make verify-scenarios`, `make test-aso`.

## Pytest And Runtime Gotchas
- `pytest.ini` disables `anyio`, `pytest-playwright`, and `pytest-base-url`. Do not assume those plugins' fixtures or CLI behavior are available.
- Runtime defaults come from checked-in `settings_cli.py`. `--server-name`, `--reference-host`, and `--base-url` override them for one run; otherwise tests use the checked-in defaults.
- `BASE_URL` / `BASE_URL_OVERRIDE` come from env or `.env`, but `server_name` comes from `settings_cli.py` unless you pass `--server-name`.
- Collection is strict for `qa/e2e/netcorner/**` and `qa/visual/**`: if target resolution cannot be inferred from path mapping, collection fails. Add `@pytest.mark.target("<id>")` or extend `framework.targeting.registry`.
- `make verify-discovery` is a real guard, not a no-op: it shells out to `pytest --collect-only -q` and fails on collection errors, timeouts, zero tests, or `MIN_EXPECTED_TESTS` underflow.

## Visual And Artifacts
- Visual outputs live under `artifacts/<run_id>/visual/`; the report server default port is `4173`.
- `npm run build` in `framework/visual/ui` runs Vitest with coverage before bundling. `npm run build:fast` skips tests and just creates the `dist/` bundle used by CI and `make report-serve`.

## Workflow Traps
- If a local commit is blocked unexpectedly, check `.git/hooks/pre-commit`: the repo provides `tools/hooks/pre-commit-aso.sh`, which runs `make test-aso`.
- Exclude `.opencode/node_modules/` from searches; it is local OpenCode plugin noise, not product code.
- README files mention targets such as `debug-minio-up`, `debug-remote-grid-up`, and `clean-visual-baselines`, but those targets are not defined in the checked-in root `Makefile`.
