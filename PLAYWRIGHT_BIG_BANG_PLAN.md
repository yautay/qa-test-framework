# PLAYWRIGHT_BIG_BANG_PLAN.md

## Goal
- [ ] Playwright + pytest (sync), stable E2E + API, CI + xdist ready.
- [ ] One test = one Playwright context.
- [ ] Run-scoped artifacts: trace/screenshot/video/logs.
- [ ] Loguru + reporting API (`start`, `test-result`, `finish`).
- [ ] Fail diagnostics: raw+annotated screenshot, best-effort highlight, min 30s video, trace.
- [ ] Quality/security/discovery gates active.
- [ ] Visual regression pillar active (`qa/visual`) with local reports and baseline strategy.
- [ ] Config validation (`scenario` + `visual`) integrated into ASO checks.

## Current decisions
- [x] Full legacy code moved under `legacy/`.
- [x] New implementation starts from scratch in `framework/` + `qa/`.
- [x] Migration pause point defined: stop before porting concrete legacy test suites.

## Env contract
- [x] `BROWSER=chromium|firefox|webkit`
- [x] `HEADLESS=0|1`
- [x] `BASE_URL`
- [x] `RECORD_VIDEO=0|1`
- [x] `VIDEO_MIN_SECONDS=30`
- [x] `REPORTING_API_URL`
- [x] `REPORTING_API_TOKEN`
- [x] `ARTIFACTS_DIR=artifacts`
- [x] `HIGHLIGHT_ON_FAIL=1`
- [x] `MIN_EXPECTED_TESTS` (default `1`)
- [x] `IS_GRID_AVAILABLE=0|1`, `GRID_WS_ENDPOINT`, `GRID_CONNECT_TIMEOUT_MS`
- [x] `REPORTING_SCHEMA_VERSION`, `REPORTING_SOURCE_PROJECT`, `REPORTING_SOURCE_ORIGIN`, `FRAMEWORK_VERSION`
- [x] `VISUAL_*` (baseline provider/profile/version, perceptual API, MinIO, fallback policy)

## Phase checklist

### Phase 0 - bootstrap
- [x] Move legacy runtime/tests/data to `legacy/`.
- [x] Create new root config: `pyproject.toml`, `pytest.ini`, `Makefile`.
- [x] Configure pytest discovery for `qa/`.
- [x] Add quality/security/discovery commands to Makefile.

### Phase 1 - Playwright runtime fixtures
- [x] Session `browser` fixture.
- [x] Function `context` fixture.
- [x] Function `page` fixture.
- [x] Start tracing always; persist trace on fail.
- [x] Video record dir run-scoped.
- [x] xdist worker context in logging setup.

### Phase 2 - framework services
- [x] `framework/env.py`.
- [x] `framework/artifacts.py`.
- [x] `framework/logger.py` (Loguru, structured).
- [x] `framework/reporting_client.py` with retry and warning-only failures.
- [x] `framework/git_info.py` CI env preferred, git fallback.

### Phase 3 - fail artifact flow
- [x] Raw full-page screenshot on fail.
- [x] Annotated screenshot with metadata overlay.
- [x] Best-effort highlight based on selector parsed from error.
- [x] Fail video preserve/trim utility (ffmpeg fallback warning).
- [x] Trace/video paths attached to test-result payload.

### Phase 4 - new PO foundation (before test migration)
- [x] `BasePage(page)` created.
- [x] Seed pages created (`login_page.py`, `orders_page.py`).
- [x] Seed data modules created.
- [ ] Port concrete legacy test suites to new `qa/` structure (SmokeTestsNUXT/TestOrders parity bridge active).

### Phase 5 - API seed
- [x] API fixture + client created.
- [x] Health-check seed test created.
- [ ] Port concrete legacy API scenarios.

### Phase 6 - visual regression foundation
- [x] New visual suite root `qa/visual` with dedicated fixtures.
- [x] Visual runner implemented (`framework/visual`) for page/element capture.
- [x] Pixel diff + local HTML/JSON report generation.
- [x] Perceptual API client integration (LPIPS/DISTS) with healthcheck + retry/fallback.
- [x] MinIO baseline provider support + local cache + approve flow.
- [x] Visual scenarios added for `hero_page`, `layers`, `product_page`.
- [x] Viewport presets extended with `mobile` and `tablet`; visual matrix via `--visual-viewports`.

### Phase 7 - tools and governance hardening
- [x] Tools reorganized by domain (`windows`, `scenarios`, `reporting`, `visual`, `remote`, `minio`, `hooks`).
- [x] Added `tools/visual/validate_scenarios.py` with configurable rules (`qa/visual/validation_rules.json`).
- [x] Naming policy enforced for visual `scenario_id` (`vrt-netcorner-nuxt-pl-*`).
- [x] `make test-aso` now includes config validation (`validate-config`) before ASO tests.
- [x] Local pre-commit hook now runs `make test-aso`.

### Phase 8 - netQArner self-test bootstrap
- [ ] Add `tools/selftest/netqarner_selftest.py` to run quick preflight diagnostics before test execution.
- [ ] Add git freshness check (`git fetch` + compare local branch against upstream) with clear warning if branch is behind.
- [ ] Add framework version check from `pyproject.toml` and print current netQArner version in self-test output.
- [ ] Add aQuArius API connectivity healthcheck (reporting base URL + key endpoint ping).
- [ ] Add visual perceptual API healthcheck (`/health`) with timeout and actionable error messages.
- [ ] Expose one command entrypoint (`make selftest`) and recommend it to testers before long runs.

### Phase 9 - compatibility removal (later)
- [ ] Remove remaining legacy compatibility from active runtime.
- [ ] Drop legacy adapter paths once suites are migrated.

## Tree checklist (new active code)

### Root
- [x] `pyproject.toml` - 100%
- [x] `pytest.ini` - 100%
- [x] `Makefile` - 100%
- [x] `settings_cli.py` - 100% (new runtime config for env URL selection)

### `framework/`
- [x] `framework/__init__.py` - 100%
- [x] `framework/env.py` - 100%
- [x] `framework/artifacts.py` - 100%
- [x] `framework/expect.py` - 100%
- [x] `framework/logger.py` - 100%
- [x] `framework/reporting_client.py` - 100%
- [x] `framework/screenshot_annotator.py` - 100%
- [x] `framework/video_utils.py` - 100%
- [x] `framework/git_info.py` - 100%
- [x] `framework/pytest_discovery_guard.py` - 100%
- [x] `framework/visual/` - 85% (runner, scenario loader, pixel compare, perceptual client, report builder, baseline store)

### `qa/`
- [x] `qa/conftest.py` - 100%
- [x] `qa/e2e/netcorner/conftest.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/pages/base_page.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/pages/login_page.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/pages/orders_page.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/pages/cart_page.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/pages/checkout_page.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/data/users.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/data/urls.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/app/data/orders.py` - 100%
- [x] `qa/e2e/netcorner/nuxt/tests/pl_komputronik/test_login_smoke.py` - 100% (seed)
- [x] `qa/e2e/netcorner/nuxt/tests/pl_komputronik/test_orders_smoke.py` - 100% (first migrated smoke suite)
- [x] `qa/api/conftest.py` - 100%
- [x] `qa/api/lib/api_interface.py` - 100%
- [x] `qa/api/tests/netcorner/promotion_service_api/test_health.py` - 100% (seed)
- [x] `qa/aso/` - 100% (technical test marker suite)
- [x] `qa/visual/netcorner/nuxt/pl/hero_page/` - 100% (homepage visual)
- [x] `qa/visual/netcorner/nuxt/pl/layers/` - 100% (login layer visual)
- [x] `qa/visual/netcorner/nuxt/pl/product_page/` - 100% (three PDP visual scenarios)
- [x] `qa/visual/validation_rules.json` - 100%

### `tools/`
- [x] `tools/windows/` - 100% (setup/cleanup + cmd wrappers)
- [x] `tools/scenarios/` - 100% (verify + report)
- [x] `tools/reporting/` - 100% (`test_api.py` + v2 contract summary endpoint)
- [x] `tools/visual/` - 85% (`sync_baseline.py`, `validate_scenarios.py`)
- [x] `tools/minio/` - 100% (local docker compose)
- [x] `tools/remote/` - 100% (playwright server docker helper)
- [x] `tools/hooks/` - 100% (ASO pre-commit installer + hook script)
- [ ] `tools/selftest/` - 0% (netQArner preflight diagnostics)

## Tree checklist (legacy archived)
- [x] `legacy/Lib/` - 100% moved
- [x] `legacy/TestCases/` - 100% moved
- [x] `legacy/TestData/` - 100% moved
- [x] `legacy/settings.py` and `legacy/settings_cli.py` - 100% moved
- [x] `legacy/conftest.py` and legacy Makefile/pytest/requirements files - 100% moved

## Validation checklist
- [x] `python -m pytest --collect-only -q`
- [x] `python framework/pytest_discovery_guard.py`
- [x] `python -m pytest qa --fixtures -q` (clean output, reporting suspended for fixtures/collect)
- [x] `python tools/visual/validate_scenarios.py`
- [x] `python tools/scenarios/verify_scenarios.py`
- [x] `make test-aso`
- [ ] `make lint`
- [ ] `make format-check`
- [ ] `make typecheck`
- [ ] `make security`
- [x] `python -m pytest qa -q` (configured environment)

## Progress log
- [x] Branch: `refactor/playwright-bigbang-basepage`
- [x] Legacy code archived under `legacy/`
- [x] New Playwright-first skeleton implemented from scratch
- [x] Started concrete migration: `legacy/.../SmokeTestsNUXT/TestOrders.py` -> `qa/.../test_orders_smoke.py`
- [x] Preserved legacy test grouping in first smoke migration (`test_order_delivery/pickup/digital/mixed`)
- [x] Added dedicated `CartPage` and `CheckoutPage` to continue smoke migration by flow blocks
- [x] Upgraded `test_order_delivery` with first real checkout-stage assertion (interactive checkout surface)
- [x] Upgraded `test_order_pickup` with first real cart-stage assertion (interactive cart surface)
- [x] Moved channel URL maps into immutable dataclass catalog in `framework/env.py` and added `settings_cli.py` URL config
- [x] Added HTTPS-cert compatibility toggle (`ignore_https_errors`) and validated working smoke on configured env
- [x] Verified working tests on configured target: `test_login_smoke` and `test_orders_smoke::test_order_delivery`
- [x] Verified full migrated smoke orders groups on configured target (`delivery/pickup/digital/mixed` all green)
- [x] Full new QA suite green on configured env (`13 passed`)
- [x] Moved locator/semantic-selector candidates into dedicated `app/selectors` module
- [x] Added legacy compatibility bridge packages (`Lib`, `TestCases`, `TestData`, `tools`, `logs`, `settings`) to run unchanged smoke flow
- [x] Implemented rewritten full-process smoke module `qa/.../test_orders_smoke_full_process.py` (no legacy test imports)
- [x] Verified full purchase process on configured env for migrated scenarios: delivery + pickup + digital samples
- [x] Replaced legacy test import approach with rewritten smoke test module using legacy PO logic + legacy test data (`test_orders_smoke_full_process.py`)
- [x] Smoke marker now maps to full-process order scenarios only (10 cases)
- [x] Validated rewritten full-process scenarios on configured env: delivery + pickup + digital samples passed
- [x] Removed runtime dependency on `legacy/` imports for smoke execution (using `ported/` code snapshot during transition)
- [x] Added Loguru timing monitor for each test case and each Playwright context lifecycle
- [x] Added timing trend tool (`framework/timing_monitor.py`) writing `artifacts/<run_id>/logs/test_durations.json` with regression warnings
- [x] Created new Playwright-native order flow stack under `qa/e2e/netcorner/nuxt/pl/app/pages` + `.../services/order_flow_service.py`
- [x] Rewrote smoke order data into native dataclasses/enums (`orders_smoke_data.py`) without legacy imports
- [ ] Finish pure Playwright full checkout submit path (`test_orders_smoke_full_process.py`) - cart-to-checkout transition still under stabilization on current env
- [x] Added reporting payload v2 envelope (`schema_version`, `event_id`, `event_type`, `idempotency_key`, `source`)
- [x] Added aQuArius handoff docs and renamed central spec namespace to `aQuArius/`
- [x] Added local remote/grid helper (`tools/remote/`) and MinIO helper (`tools/minio/`)
- [x] Added visual regression runner under `framework/visual` and suite under `qa/visual`
- [x] Added first visual scenarios split by module (`hero_page`, `layers`, `product_page`)
- [x] Added configurable visual scenario validator and integrated it with ASO checks
- [x] Reorganized `tools/` directory and updated documentation paths/commands
