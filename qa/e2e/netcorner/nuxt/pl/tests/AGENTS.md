# AGENTS.md

## Scope
- This file applies to all tests under `qa/e2e/netcorner/nuxt/pl/tests/`.
- These rules are additive to the repository root `AGENTS.md` and `docs/E2E_PAGE_OBJECT_CONTRACT.md`.

## Test Domain Responsibilities
- Keep the domain split strict: business assertions belong in tests.
- Page objects and wrappers should expose intent-driven actions and typed reads only.
- Do not place hidden `assert`/`expect` checks inside POM action methods.

## Preferred Test Structure
- Follow the existing suite pattern:
  1. Arrange data/setup (builders, generators, fixtures)
  2. Execute flow through wrappers/POM
  3. Assert explicit business outcomes in the test
- Keep scenario names and markers semantic and consistent (`pytestmark`, `@pytest.mark.scenario(...)`).

## Data And Parametrization
- Prefer typed generators/builders from `qa/e2e/netcorner/nuxt/pl/lib/test_data/**` over ad-hoc inline dicts.
- Use stable case objects (`case_id`, factory/model) and parametrize with:
  - `pytest.mark.parametrize(..., ids=lambda case: case.case_id)`
- Avoid branching multiple behavioral variants in one test when parametrization is a better fit.

## Stability Rules
- Do not add forced fallback/retry ladders in tests ("try many paths until one works") unless the UI contract explicitly defines deterministic variants.
- Avoid `time.sleep(...)`; use existing waits from page objects/wrappers and explicit UI conditions.
- Keep failures explicit and diagnostic (clear assertion messages describing business expectation vs actual result).

## Polling And Backend Waits
- For backend/API polling (waiting for a mail, OZO counter update, admin state change) use `framework.polling.poll_until` imported via `qa.e2e.netcorner.nuxt.pl.tests.helpers`.
- Do **not** write inline `while + time.sleep` or `for _ in range(n): ... wait_for_timeout(...)` polling loops in tests.
- For Playwright UI readiness use `expect(...)`, `wait_loaded()`, `wait_visible()` — not `poll_until`.
- For waiting on Mailhog mail delivery use `mail_inbox.wait_for_mails_containing_text(...)` (HTTP API polling, no browser needed).

## Timeout Constants
- Import timeout constants from `qa.e2e.netcorner.nuxt.pl.lib.timeouts` (re-export of `framework/timeouts.py`).
- Do **not** use raw integer literals for `timeout=` arguments; always reference a named constant.
- Common constants: `QUICK_PROBE_MS`, `ELEMENT_VISIBLE_MS`, `UI_ACTION_MS`, `SLOW_OPERATION_MS`, `HTTP_REQUEST_TIMEOUT_S`.
- See root `AGENTS.md` for the full tier table and exception list.
