## Scope
- This file applies to all code under `qa/e2e/netcorner/nuxt/pl/lib/page_objects/overlays/`.
- Follow `docs/E2E_PAGE_OBJECT_CONTRACT.md` as the normative rule set.

## Protected Areas (Do Not Modify By Default)
- Do not modify `conftest.py` at repository root.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify anything under `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- These are out of scope unless explicitly requested by the user.

## Overlay Responsibilities
- Overlay objects represent modal/popup/toast layers above a page.
- Each overlay must own a clear root locator for the visible layer.
- Keep overlay APIs focused on user intent (open/fill/confirm/close/read state).
- Overlay methods should not contain unrelated page navigation logic.

## Boundary And Locator Rules
- Operate inside overlay root (`self.root`) by default.
- Prefer stable domain attributes and semantic Playwright locators.
- Use text locators only when business text is stable and intentional.
- Use CSS/XPath only if stronger contracts are unavailable.

## Optionality And Resilience
- Optional overlays are allowed when they are part of real UI contract.
- Optional handling must be explicit and bounded (clear timeout, clear boolean/result).
- Fail with clear error when required overlay contract is not met.

## No-Fallback Policy
- Do not add silent fallback locator chains.
- Do not hide contract problems with broad exception handling.
- Do not implement alternate hidden click paths unless UI contract explicitly requires variants.

## API And Typing Style
- Keep typed method signatures and returns.
- Return domain data (typed values/dataclasses) from read methods.
- Do not expose raw locators to tests/wrappers.

## Step And Wait Rules
- Use `step` from `qa.e2e.netcorner.lib.step_api`.
- Do not import `allure.step` directly.
- Use `wait_visible` and `wait_hidden` for lifecycle synchronization.
- Avoid `sleep(...)`.

## Legacy Touch Policy
- When touching legacy overlays, migrate touched logic toward explicit root scoping and no-fallback behavior.
- Keep retries bounded and intentional.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests`
