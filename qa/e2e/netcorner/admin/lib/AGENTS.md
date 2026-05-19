## Scope
- This file applies to `qa/e2e/netcorner/admin/lib/` and all nested folders.
- Directory-specific instructions in nested `AGENTS.md` files are additive and must also be followed.
- Normative contract: `docs/E2E_PAGE_OBJECT_CONTRACT.md`.

## Layer Responsibilities
- `page_objects/`: deterministic UI interactions and typed reads for admin panel views.
- `flows/`: orchestration and reusable admin workflows.
- `test_data/`: typed test contracts and reusable data models.

## Non-Negotiable Rules
- Keep domain split strict: assertions belong in tests.
- Keep APIs intent-driven; avoid exposing raw locators.
- Prefer explicit waits and stable locators over brittle selectors.
- No silent fallback chains, no broad exception swallowing.

## Admin Panel Semantics
- Admin is a server-rendered app (`admin.php` routes), not SPA.
- Prefer stable `id`-based locators where available.
- Keep page readiness checks explicit and deterministic.

## Step And Wait Standards
- Use project step wrappers; do not import `allure.step` directly in admin page objects.
- Avoid `sleep(...)`; use explicit waits (`wait_loaded`, visible/hidden checks, expectations).

## Protected Areas (Do Not Modify By Default)
- Do not modify repository root `conftest.py`.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- Modify these only when explicitly requested by the user.

## Legacy Touch Policy
- When touching legacy code, migrate touched area toward explicit contracts.
- Do not preserve ambiguity to "make tests pass".

## Verification Baseline
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/admin/lib`
