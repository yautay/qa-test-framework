## Scope
- This file applies to `qa/e2e/netcorner/admin/lib/page_objects/`.
- Directory-specific instructions in nested `AGENTS.md` files are additive and must also be followed.
- Normative contract: `docs/E2E_PAGE_OBJECT_CONTRACT.md`.

## Layer Responsibilities
- `pages/`: full-screen admin views, transitions, and page readiness.
- `base_page.py`: shared base behavior and contracts for admin pages.

## Page Object Rules
- Keep methods intent-driven and business-semantic.
- Keep methods small, typed, and single-purpose.
- Do not expose raw locators in public APIs.
- Do not put scenario business assertions in page object methods.

## Boundary And Locator Rules
- Prefer stable admin locators (`id`, stable names, deterministic attributes).
- Use semantic Playwright locators where they improve clarity.
- Use CSS/XPath only when stronger contracts are unavailable.
- Avoid broad selectors spanning unrelated containers.

## No-Fallback Policy
- Do not add silent fallback chains.
- Do not hide locator/contract failures with broad exceptions.
- Keep optional behavior explicit and bounded.

## Step And Wait Rules
- Use project step wrappers where page objects expose actions.
- Avoid `sleep(...)`; prefer explicit waits and expectations.

## Legacy Touch Policy
- If you touch legacy POM code, migrate touched area toward contract compliance.
- Do not increase ambiguity or hidden resilience.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/admin/lib`
