# AGENTS.md

## Scope
- Python runtime is 3.13. Use `python -m pip install -e ".[dev]"` for backend/dev dependencies.
- The only separate Node project is `framework/visual/ui` (CI uses Node 22 there). Run `npm ci` inside that directory; the repo root is not a Node workspace.
- `qa/aso/framework/**` is the main framework regression/unit-style suite for `framework/`; most backend tests are there, not under a top-level `tests/` directory.

## Verified Commands
- Root `Makefile` is the source of truth for Python commands. Check `make help` before trusting README command lists.
- Prefer `make ...` targets or `.venv/bin/python -m ...` for all Python test/lint commands. Do not use plain `python`, `pytest`, or `pip` from the system shell, because that can silently pick the wrong interpreter.
- Fast sanity check before any Python test run: `make help`, `.venv/bin/python --version`, then run either `make <target>` or `.venv/bin/python -m pytest ...`.
- If you need a direct pytest invocation for a focused file, use `.venv/bin/python -m pytest <path> -q` from repo root.
- Full Python verification is `make check`, in this order: `test-aso -> lint -> format-check -> typecheck -> security -> verify-discovery -> verify-scenarios -> collect`.
- Focused suites: `make test-aso`, `make test-e2e`, `make test-api`, `make test-visual`, `make test-smoke`.
- `make check` does not cover the Vue report UI. If you touch `framework/visual/ui`, also run `npm run test:unit` and `npm run build:fast` in `framework/visual/ui` to match CI.
- `make report-serve` only starts the Python report server. It fails if `framework/visual/ui/dist` is missing; build the UI first with `npm run build` or `npm run build:fast` in `framework/visual/ui`.
- CI ASO parity env: `HEADLESS=1 IS_GRID_AVAILABLE=0 REPORTING_ENABLED=0 ALLURE_ENABLED=0 PYTEST_HTML_ENABLED=0 RECORD_VIDEO=0` before `make verify-discovery`, `make verify-scenarios`, `make test-aso`.

## Pytest And Runtime Gotchas
- Repo-local interpreter is `.venv/bin/python`; it must resolve to Python 3.13. If not, stop and fix the environment before debugging tests.
- A failed import like `cannot import name 'UTC' from 'datetime'` means the wrong interpreter was used; switch immediately to `.venv/bin/python -m pytest ...` or `make ...`.
- `pytest.ini` disables `anyio`, `pytest-playwright`, and `pytest-base-url`. Do not assume those plugins' fixtures or CLI behavior are available.
- Runtime defaults come from checked-in `settings_cli.py`. `--server-name`, `--reference-host`, and `--base-url` override them for one run; otherwise tests use the checked-in defaults.
- `BASE_URL` / `BASE_URL_OVERRIDE` come from env or `.env`, but `server_name` comes from `settings_cli.py` unless you pass `--server-name`.
- Collection is strict for `qa/e2e/netcorner/**` and `qa/visual/**`: if target resolution cannot be inferred from path mapping, collection fails. Add `@pytest.mark.target("<id>")` or extend `framework.targeting.registry`.
- `make verify-discovery` is a real guard, not a no-op: it shells out to `pytest --collect-only -q` and fails on collection errors, timeouts, zero tests, or `MIN_EXPECTED_TESTS` underflow.

## Visual And Artifacts
- Visual outputs live under `artifacts/<run_id>/visual/`; the report server default port is `4173`.
- `npm run build` in `framework/visual/ui` runs Vitest with coverage before bundling. `npm run build:fast` skips tests and just creates the `dist/` bundle used by CI and `make report-serve`.
- Full artifact layout and debugging workflows (logs, traces, DOM snapshots, screenshots) are documented in `docs/DEBUG_AGENTS.md`. **Read that file first when diagnosing a failing E2E test.**

## Test Environment Connectivity
- Test environments use internal netcorner.pl domains (e.g. `komputronik-galak.test.netcorner.pl`). VPN is required.
- The TLS certificate is issued by an internal CA not trusted by the system store. Use `curl -sk` or Playwright's `ignore_https_errors=True` (already set via `RuntimeEnv.ignore_https_errors`).
- **`server_name` in `settings_cli.py` is `"galak.test"`** — this is the token passed to `resolve_admin_env()` and `resolve_mail_inbox_env()`.
- Frontend URL: `https://komputronik-galak.test.netcorner.pl/` (base_url from `settings_cli.py`).
- Admin panel URL: `https://admin-galak.test.netcorner.pl/admin.php` — constructed by `resolve_admin_env("galak.test")` in `qa/e2e/netcorner/admin/lib/config.py`.
- Admin credentials: login `at.tester`, password `p3yEna8GfA7GdMR8TBKTm4myT7` (base64-decoded from `nc-functional-tests-py/settings.py`). Do not use `root`/komercja credentials.
- Admin sales channel for PL tests: `id=1` (komputronik.pl). Selected via `AdminContextPage.select_context(1)`.
- Mailhog URL: `https://mail-galak.test.netcorner.pl` — resolved via `resolve_mail_inbox_env("galak.test")`.
- Connectivity check: `curl -skL -o /dev/null -w "%{http_code}" <url>` — expect `200` or `302` when VPN is active.
- To verify admin access from scripts: use `playwright.sync_api` with `ignore_https_errors=True` in browser context — the standard test setup already sets this via `RuntimeEnv.ignore_https_errors`.
- **Admin HTML quirks confirmed live (2026-05-14):**
  - `id="productBruttoSum"` appears twice (brutto + netto bug) — always use `.first`.
  - Order list links: use `a[href*='order_id']:not([title=''])` to skip edit-icon duplicates.
  - Order comment element: `id="salesman_comment"` (not `.form-row`).
  - Status change: clicking `#orderStatus > a` triggers AJAX that injects `select[id*='status_id']`.

## Workflow Traps
- Exclude `.opencode/node_modules/` from searches; it is local OpenCode plugin noise, not product code.
- README files mention targets such as `debug-minio-up`, `debug-remote-grid-up`, and `clean-visual-baselines`, but those targets are not defined in the checked-in root `Makefile`.

## E2E Page Object Contract
- For `qa/e2e/**`, follow `docs/E2E_PAGE_OBJECT_CONTRACT.md`.
- Do not introduce new silent fallback chains in page objects or wrappers.
- Prefer root-scoped locators and semantic Playwright locators over global page lookups.
- When touching legacy E2E page objects, migrate the touched area toward the contract instead of preserving ambiguous fallback behavior.
