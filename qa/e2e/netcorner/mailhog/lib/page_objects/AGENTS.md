## Scope
- This file applies to `qa/e2e/netcorner/mailhog/lib/page_objects/`.
- Directory-specific instructions in nested `AGENTS.md` files are additive and must also be followed.
- Normative contract: `docs/E2E_PAGE_OBJECT_CONTRACT.md`.

## Layer Responsibilities
- `pages/`: full-screen inbox/login views, page transitions, and page readiness.
- Keep page object APIs focused on user intent and typed reads.

## Non-Negotiable Rules
- Keep methods small, typed, and single-purpose.
- Keep POM methods free of business assertions (`assert`/`expect`).
- Do not expose raw locators to tests or wrappers.
- Do not add hidden fallback/retry chains.

## Locator And Boundary Rules
- Respect page object boundaries; keep logic in object-local methods.
- Prefer stable and semantic locators first.
- Use CSS/XPath only when stronger contracts are unavailable.

## Step And Wait Standards
- Use local `step` wrappers from `qa.e2e.netcorner.mailhog.lib.allure_decorators`.
- Avoid `sleep(...)`; use deterministic waits and explicit UI conditions.

## Legacy Touch Policy
- When touching legacy POM code, migrate touched area toward the contract.
- Do not increase ambiguity or hidden resilience.

## Verification Baseline
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/mailhog/lib`
