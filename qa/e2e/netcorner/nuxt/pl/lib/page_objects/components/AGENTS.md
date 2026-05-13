## Scope
- This file applies to all code under `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/`.
- Follow `docs/E2E_PAGE_OBJECT_CONTRACT.md` as the mandatory contract.

## Protected Areas (Do Not Modify By Default)
- Do not modify `conftest.py` at repository root.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify anything under `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- Update these only when explicitly requested by the user.

## Component Construction Pattern
- Components must inherit from local `BaseComponent`.
- Define `ROOT_SELECTOR` whenever possible.
- Constructor should follow:
  - `super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="...")`
- Accept `scope: Page | Locator` for reusable composition.

## Root Boundary Contract
- Component logic must stay within `self.root`.
- Use `self.find(...)` for first-level descendants of `self.root`.
- Use `self.root.get_by_*` for semantic locators scoped to root.
- For nested areas, cache parent locators and continue from parent scope.
- Do not jump to `self.root.page` unless intentionally leaving component boundary.

## Locator Strategy
- Preferred order:
  1. Stable domain attributes (`data-name`, `data-role`, `data-picker`)
  2. Semantic Playwright locators (`get_by_role`, `get_by_label`, `get_by_text`)
  3. Stable business text
  4. CSS/XPath only if needed

## Public API Design
- Expose business-intent methods (`fill_*`, `set_*`, `choose_*`, `submit_*`, `get_*`).
- Keep methods single-purpose.
- In-place mutating methods should return `Self`.
- Data reads should return typed values/dataclasses, not locators.
- Keep locators private (`self.__...`) in components.

## Click/Input/Wait Rules
- Prefer shared helpers: `pointer_click`, `safe_fill`, `safe_type`.
- Avoid redundant pre-checks if helper already validates state.
- Avoid `sleep(...)`; use expectations and explicit waits.

## No-Fallback Policy
- Do not add new silent fallback chains.
- Forbidden defaults:
  - `if not found -> use unrelated locator`
  - broad `except Exception` around interaction logic
  - trial click path followed by real click without explicit UI contract

## Step And Reporting
- Import `step` from `qa.e2e.netcorner.lib.step_api`.
- Do not import `allure.step` directly in component code.

## Legacy Touch Policy
- When modifying legacy components, move touched code toward strict root scoping and explicit contracts.
- Do not keep ambiguity for convenience.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests`
