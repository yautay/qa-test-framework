## Scope
- This file applies to `qa/e2e/netcorner/mailhog/lib/` and all nested folders.
- Directory-specific instructions in nested `AGENTS.md` files are additive and must also be followed.
- Normative contract: `docs/E2E_PAGE_OBJECT_CONTRACT.md`.

## Layer Responsibilities
- `page_objects/`: deterministic UI interactions and typed reads.
- `flows/`: orchestration of inbox scenarios across page objects and runtime context.
- `config.py` and `mail_subjects.py`: environment and subject contracts; keep them explicit and stable.

## Non-Negotiable Rules
- Keep domain split strict: assertions belong to tests, not page objects.
- Keep APIs intent-driven; do not expose raw locators to tests.
- Prefer explicit waits and deterministic timeout behavior over hidden retries.
- Do not add silent fallback chains or broad exception swallowing.

## Locator And Wait Standards
- Prefer stable/semantic locators over brittle CSS/XPath chains when possible.
- Avoid `sleep(...)`; use explicit UI conditions and contract-based waits.
- Use bounded optionality only when the UI contract explicitly defines optional branches.

## Step And Reporting Rules
- Use local step wrappers from `qa.e2e.netcorner.mailhog.lib.allure_decorators`.
- Keep step names business-semantic and stable.
- Do not introduce ad-hoc reporting layers for single methods.

## Legacy Touch Policy
- When touching legacy code, migrate touched area toward explicit contracts.
- Do not preserve ambiguity only to "make tests pass".

## Protected Areas (Do Not Modify By Default)
- Do not modify repository root `conftest.py`.
- Do not modify `qa/e2e/netcorner/nuxt/pl/conftest.py`.
- Do not modify `framework/**`.
- Do not modify `pytest.ini` or `settings_cli.py`.
- Modify these only when explicitly requested by the user.

## Verification Baseline
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/mailhog/lib`
