## Scope
- This file applies to all code under `qa/e2e/netcorner/mailhog/lib/page_objects/pages/`.
- Follow `docs/E2E_PAGE_OBJECT_CONTRACT.md` as the source of truth.

## Page Object Rules
- A page class must represent a full screen and be named `*Page`.
- Keep `PATH` when the page has a stable route.
- Keep page methods business-oriented and intent-driven.
- When action changes screen context, return a loaded page object when practical.
- Do not expose raw locators from page classes.

## Provider-Aware Behavior
- Provider differences (MailHog vs Roundcube) are allowed only as explicit, bounded branches.
- Keep provider-specific selectors localized and easy to audit.
- Do not add unbounded fallback ladders across providers.

## Boundary And Locator Rules
- Prefer stable attributes and semantic Playwright locators first.
- Use stable text locators only when business text is intentional and stable.
- Use CSS/XPath only as a last resort.

## Step And Wait Rules
- Use step wrappers from `qa.e2e.netcorner.mailhog.lib.allure_decorators`.
- Avoid `sleep(...)`; use explicit waits and deterministic timeouts.
- Keep failure messages contract-oriented and diagnostic.

## Typing And API Style
- Keep full type hints for inputs and returns.
- Return domain values (e.g. `str`, `bool`, typed objects), never locators, from public APIs.
- Keep methods small and single-purpose.

## Legacy Touch Policy
- If you touch legacy page code, migrate the touched area toward contract compliance.
- Do not preserve or add ambiguous fallback behavior.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/mailhog/lib`
