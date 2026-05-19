## Scope
- This file applies to all code under `qa/e2e/netcorner/admin/lib/page_objects/pages/`.
- Follow `docs/E2E_PAGE_OBJECT_CONTRACT.md` as the source of truth.

## Page Object Rules
- A page class represents one full admin view and should be named `*Page`.
- Keep stable `PAGE_ID` in format `netcorner.admin.<view>`.
- Keep `PATH` for pages with stable routes.
- Implement deterministic `wait_loaded(...)` for page readiness.
- Keep navigation/actions business-oriented and explicit.

## Admin SSR Constraints
- Admin uses server-rendered HTML; rely on deterministic load states.
- Prefer stable `id`-based selectors for key controls.
- Keep known HTML quirks handled explicitly and locally.

## Boundary And Locator Rules
- Keep interactions scoped to page contracts and child objects.
- Prefer stable attributes and semantic locators first.
- Avoid brittle selector chains and ambiguous text-only fallbacks.

## Step, Wait, And API Style
- Use project step wrappers where actions are exposed.
- Avoid `sleep(...)`; use `wait_loaded`, visible/hidden checks, explicit expectations.
- Keep full type hints and return typed values/objects, not locators.

## No-Fallback Policy
- No silent fallback chains.
- No broad exception swallowing around interactions.
- Optional flows must be bounded and contract-defined.

## Legacy Touch Policy
- If touching legacy pages, migrate touched area toward strict contract behavior.
- Do not preserve ambiguous resilience paths.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/admin/lib`
