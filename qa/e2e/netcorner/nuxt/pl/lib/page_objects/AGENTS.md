## Scope
- This file applies to `qa/e2e/netcorner/nuxt/pl/lib/page_objects/` and provides shared rules.
- Directory-specific instructions in nested `AGENTS.md` files are additive and must also be followed.
- Normative contract: `docs/E2E_PAGE_OBJECT_CONTRACT.md`.

## Layer Responsibilities
- `pages/`: full-screen objects, transitions, and page readiness.
- `sections/`: major page areas that compose child components.
- `components/`: focused UI building blocks with strict root scoping.
- `overlays/`: modal/popup/toast layers with explicit lifecycle handling.

## Non-Negotiable Rules
- Respect root boundaries: interact within local root by default.
- Use stable locators first (`data-name`, `data-role`, `data-picker`).
- Prefer semantic Playwright locators over brittle CSS/XPath when possible.
- Keep APIs intent-driven; do not expose raw locators to tests.
- Keep methods small, typed, and single-purpose.
- No silent fallback chains, no broad exception swallowing for locator failures.

## Step And Wait Standards
- Use `step`/`step_context` from `qa.e2e.netcorner.lib.step_api`.
- Do not import `allure.step` directly in page object code.
- Avoid `sleep(...)`; use explicit waits (`wait_loaded`, `wait_visible`, `wait_hidden`, `expect`).

## Protected Areas (Do Not Modify By Default)
- Do not modify repository root `conftest.py`.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- Modify these only when explicitly requested by the user.

## Legacy Touch Policy
- When touching legacy code, migrate the touched area toward the contract.
- Do not add ambiguity or hidden resilience to "make tests pass".

## Verification Baseline
- Minimum after page object changes:
  - `python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests`
