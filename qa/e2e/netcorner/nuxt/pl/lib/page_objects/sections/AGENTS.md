## Scope
- This file applies to all code under `qa/e2e/netcorner/nuxt/pl/lib/page_objects/sections/`.
- Follow `docs/E2E_PAGE_OBJECT_CONTRACT.md` as the normative contract.

## Protected Areas (Do Not Modify By Default)
- Do not modify `conftest.py` at repository root.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify anything under `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- Change these only if explicitly requested by the user.

## Section Responsibilities
- A section groups a major page area (`Header`, `Navigation`, `Content`, `Footer`).
- A section owns one clear root and composes child components from that root.
- Keep sections thin: composition + routing of intent, not heavy business logic.
- Use lazy child initialization via properties.

## Boundary Rules
- A section must not escape its root to query global page state.
- Child components must be initialized with section root scope.
- Do not resolve locators from `page` when section root is available.

## Locator Rules
- Preferred order: stable domain attributes -> semantic Playwright locators -> stable text -> CSS/XPath as last resort.
- Keep selectors local and meaningful.
- Avoid long brittle selectors spanning unrelated containers.

## No-Fallback Policy
- Do not add silent fallback chains.
- Avoid patterns like:
  - "try primary, else secondary" without explicit UI contract.
  - broad exception swallowing around locator actions.
  - hidden retries that mask broken contracts.

## Step, Wait, And API Style
- Use step wrappers from `qa.e2e.netcorner.lib.step_api` when sections expose actionable methods.
- Prefer `wait_visible()` for section readiness.
- Keep section methods intent-driven and minimal.
- Never expose raw locators through section public API.

## Legacy Touch Policy
- If touching legacy section code, improve only touched area toward contract compliance.
- Do not increase ambiguity or scope leakage.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests`
