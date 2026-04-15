# Generate E2E test from scenario

Input:

- SERVER_NAME: $SERVER_NAME
- SCENARIO_PROMPT: $SCENARIO_PROMPT
- JOB_ID: $JOB_ID

Task:

1. Focus only on E2E (`qa/e2e/`), especially `qa/e2e/netcorner/nuxt/pl/`.
2. Build target URL only via runtime resolution (`--server-name=$SERVER_NAME`), no hardcoded host in code.
3. Reuse existing analysis artifacts first before any new DOM fetching:
   - if `JOB_ID` is provided, read `work/e2e-jobs/$JOB_ID/analysis/` and `work/e2e-jobs/$JOB_ID/handoff/analysis_contract.json`
   - otherwise check `.opencode/dom-cache/**/latest/` for matching `SERVER_NAME`
   - only if cache is missing, ask user to run `project:e2e:job:analyze` or `project:e2e:analyze_dom_and_refine_scenario`
4. Reuse existing architecture and style from current tests and POM.
5. Use strict POM chain: `page.section.component.method`.
6. Keep locators and UI logic in PO/components, not in test function.
7. Public PO methods must use Steps API `@step(...)` (`qa.e2e.netcorner.nuxt.pl.lib.allure_decorators.step`).
8. Reuse existing wrappers first, especially:
   - `qa/e2e/netcorner/nuxt/pl/lib/flows/client_wrappers.py`
9. Add new wrapper only when action is a reusable composition of many POM calls (complex repeated flow).
10. Do not create unused Page Objects, sections, components, or methods.
11. For Component classes only, apply recommendations from `qa-test-tools/lokomokopom` when available.
12. Keep changes minimal and aligned with existing naming/import style.

Implementation details:

- Place test in the best matching module under `qa/e2e/netcorner/nuxt/pl/tests/` inferred from scenario.
- Apply markers in existing style (`pytestmark`, `@pytest.mark.scenario(...)`, optional parametrize).
- For auth setup, follow established `ClientWrappers` patterns.

Validation:

1. Run `make verify-discovery`.
2. Run targeted pytest for the new test with server selector:
   - `python -m pytest <new_test_path> -q --server-name=$SERVER_NAME`

Return:

- changed files,
- why each file changed,
- exact validation commands and status.
