# AGENTS.md

## Scope
- Python runtime is 3.13. Use `python -m pip install -e ".[dev]"` for backend/dev dependencies.
- The only separate Node project is `framework/visual/ui` (CI uses Node 22 there). Run `npm ci` inside that directory; the repo root is not a Node workspace.
- `qa/aso/framework/**` is the main framework regression/unit-style suite for `framework/`; most backend tests are there, not under a top-level `tests/` directory.

## Nested AGENTS Guides
- `qa/e2e/netcorner/nuxt/pl/tests/AGENTS.md`
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/AGENTS.md`
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/AGENTS.md`
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/overlays/AGENTS.md`
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/pages/AGENTS.md`
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/sections/AGENTS.md`
- `qa/e2e/netcorner/nuxt/pl/lib/test_data/AGENTS.md`
- `qa/e2e/netcorner/mailhog/lib/AGENTS.md`
- `qa/e2e/netcorner/mailhog/lib/page_objects/AGENTS.md`
- `qa/e2e/netcorner/mailhog/lib/page_objects/pages/AGENTS.md`
- `qa/e2e/netcorner/mailhog/lib/flows/AGENTS.md`
- `qa/e2e/netcorner/admin/lib/AGENTS.md`
- `qa/e2e/netcorner/admin/lib/page_objects/AGENTS.md`
- `qa/e2e/netcorner/admin/lib/page_objects/pages/AGENTS.md`
- `qa/e2e/netcorner/admin/lib/flows/AGENTS.md`
- `qa/e2e/netcorner/admin/lib/test_data/AGENTS.md`

## Verified Commands
- Root `Makefile` is the source of truth for Python commands. Check `make help` before trusting README command lists.
- Prefer `make ...` targets or `.venv/bin/python -m ...` for all Python test/lint commands. Do not use plain `python`, `pytest`, or `pip` from the system shell, because that can silently pick the wrong interpreter.
- Fast sanity check before any Python test run: `make help`, `.venv/bin/python --version`, then run either `make <target>` or `.venv/bin/python -m pytest ...`.
- If you need a direct pytest invocation for a focused file, use `.venv/bin/python -m pytest <path> -q` from repo root.
- Full Python verification is `make check`, in this order: `test-aso -> lint -> format-check -> typecheck -> security -> verify-discovery -> verify-scenarios -> collect`.
- Focused suites: `make test-aso`, `make test-e2e`, `make test-api`, `make test-visual`, `make test-smoke`.
- Setup suite: `make test-setup` (Netcorner SetUpNUXT parity for environment/data seeding).
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
- Marker inventory helper: run `.venv/bin/python tools/pytest/generate_marker_matrix.py` to regenerate `docs/MARKER_TESTS_MATRIX.md` (marker -> test mapping). Refresh after marker/test taxonomy changes.

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
- On every new test environment, run `make test-setup` before running dependent Netcorner E2E suites.
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
- **Never commit `settings.py` or `settings_cli.py`** — these are local run-configuration files (environment, browser, server_name, credentials overrides). Changes to them are per-developer and must stay unstaged.

## E2E Page Object Contract
- For `qa/e2e/**`, follow `docs/E2E_PAGE_OBJECT_CONTRACT.md`.
- Do not introduce new silent fallback chains in page objects or wrappers.
- Do not implement click/wait retry fallbacks in page objects (e.g. `try open+wait, except: open+wait`). Fix the underlying locator/readiness contract instead.
- Do not introduce forced fallback/retry ladders in E2E tests ("try a few alternative paths until one passes") unless a documented, deterministic UI contract explicitly requires variants.
- Prefer root-scoped locators and semantic Playwright locators over global page lookups.
- When touching legacy E2E page objects, migrate the touched area toward the contract instead of preserving ambiguous fallback behavior.

## E2E Test Authoring Best Practices
- Domain split must stay strict: **assertions belong to tests**, while page objects/wrappers expose intent-driven actions and typed reads only.
- Do not move business assertions into POM methods (no hidden `expect(...)` / `assert` in page object action APIs).
- Keep test structure aligned with existing suites (arrange data/setup -> execute flow via wrappers/POM -> assert explicit business outcomes).
- Use semantic scenario naming and markers (`@pytest.mark.scenario(...)`, `pytestmark`) consistent with neighboring tests.
- Prefer explicit, typed test data from generators/builders in `lib/test_data/**` over inline ad-hoc dicts.
- Parameterize behavior variants with `pytest.mark.parametrize(..., ids=lambda case: case.case_id)` and stable case objects (`case_id`, factory/data model) instead of branching logic inside one test.
- Do not add `sleep(...)` / `wait_for_timeout(...)` as environment-level stabilizers in tests; they mask readiness/contract issues. Temporary sleeps are allowed only for a test currently being debugged and must be removed before finalizing changes.

## Polling And Backend Waits
- Use `framework.polling.poll_until` for all backend/API polling (Mailhog API, OZO counters, admin state changes). Do **not** write inline `while + time.sleep` loops in tests or flows.
- Use `framework.polling.HttpPoller` for polling HTTP JSON endpoints (e.g. Mailhog `/api/v2/search`). Do **not** call `urllib.request.urlopen` directly in test or flow code.
- `poll_until` / `HttpPoller` are for backend resources. For Playwright UI readiness use `expect(...)`, `wait_loaded()`, and `wait_visible()` — not `poll_until`.
- Mailhog inbox has **two access paths** with different contracts:
  - **HTTP API** (`MailhogApiClient` in `qa/e2e/netcorner/mailhog/lib/api/mailhog_api_client.py`): fast, no browser required, use for counting/searching mails by order number.
  - **Playwright UI** (`MailInboxService` in `qa/e2e/netcorner/mailhog/lib/flows/inbox_flow.py`): browser-based, use for reading mail content and extracting links.
- Do not mix HTTP API and Playwright UI access inside a single method without documenting the reason.

## Timeout Constants
- All Playwright and HTTP timeout values must use named constants from `framework/timeouts.py` (or per-project re-exports). Do **not** use raw integer literals for timeouts.
- Per-project re-exports (import from these in project code):
  - `qa.e2e.netcorner.nuxt.pl.lib.timeouts`
  - `qa.e2e.netcorner.admin.lib.timeouts`
  - `qa.e2e.netcorner.mailhog.lib.timeouts`
  - `qa.e2e.netcorner.setup.timeouts`
- Tier mapping:

  | Constant                  | Value      | Use for                                               |
  |---------------------------|------------|-------------------------------------------------------|
  | `QUICK_PROBE_MS`          | 2 000 ms   | Short probes, animation settle, minor UI transitions  |
  | `ELEMENT_VISIBLE_MS`      | 5 000 ms   | Element visibility checks, toast waits                |
  | `UI_ACTION_MS`            | 15 000 ms  | Navigation, overlay open/close, URL waits             |
  | `SLOW_OPERATION_MS`       | 30 000 ms  | Heavy page loads, AJAX-heavy operations               |
  | `HTTP_REQUEST_TIMEOUT_S`  | 30 s       | `requests` / HTTP client calls (seconds, not ms)      |

- Exceptions (keep as-is, do **not** replace with tier constants):
  - `_REINDEX_TIMEOUT_MS = 120_000`
  - `_PROMOTION_SERVICE_ACTIVATION_WAIT_MS = 120_000`
  - `_MAILHOG_LOOKUP_TIMEOUT_MS = 45_000`
