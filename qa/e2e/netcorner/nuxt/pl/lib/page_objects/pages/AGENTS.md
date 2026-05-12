## Scope
- This file applies to all code under `qa/e2e/netcorner/nuxt/pl/lib/page_objects/pages/`.
- Follow `docs/E2E_PAGE_OBJECT_CONTRACT.md` as the source of truth.
- Use `docs/PAGE_OBJECTS_EN.md` as a style and onboarding guide.

## Protected Areas (Do Not Modify By Default)
- Do not modify `conftest.py` at repository root.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify anything under `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- These files may be changed only when the user explicitly asks for it.

## Page Object Rules
- A page class must represent a full screen and be named `*Page`.
- Keep `PATH` when the page has a stable route.
- Implement `wait_loaded(...)` and validate page readiness via visible key sections/components.
- Expose page sections through lazy properties (`header`, `navigation`, `content`, `footer`).
- Keep page methods business-oriented (`open_register_page`, `open_account_page`).
- When action changes screen context, return a new page object (already loaded).
- Do not expose raw locators from page classes.

## Boundary And Locator Rules
- Respect root boundaries; pages compose sections, sections compose components.
- Do not bypass component boundaries from page methods.
- Prefer stable domain locators (`data-name`, `data-role`, `data-picker`).
- Prefer semantic Playwright locators (`get_by_role`, `get_by_label`, `get_by_text`) over CSS/XPath when clear.
- Do not add silent fallback chains (`if count==0 use backup`, broad `except Exception`, hidden retry ladders).

## Step And Wait Rules
- Use step wrappers only from `qa.e2e.netcorner.lib.step_api`.
- Do not import `allure.step` directly inside page objects.
- Avoid `sleep(...)`; use `wait_loaded`, `wait_visible`, and explicit expectations.

## Typing And API Style
- Keep full type hints for inputs and returns.
- Use `| None` for optional returns.
- Return data objects or primitives, never locators, from public API.
- Keep methods small and single-purpose.

## Legacy Touch Policy
- If you touch legacy page code, migrate the touched area toward the contract.
- Do not preserve or add ambiguous fallback behavior just to make tests pass.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests`
- Run focused pytest suites relevant to changed pages when possible.
