# E2E subagent: reviewer

Input:

- SERVER_NAME: $SERVER_NAME
- TARGET_TEST_PATH: $TARGET_TEST_PATH

Task:

Use the `agent` tool once as quality gate reviewer for generated E2E test.

Check:

1. E2E scope only.
2. POM chain `page.section.component.method`.
3. No locator usage in test files.
4. Public PO methods use `@step(...)`.
5. No unused PO classes/methods introduced.
6. Runtime URL flow based on `runtime_env.base_url` and `--server-name=$SERVER_NAME`.
7. Markers/scenario decorators align with existing suite.
8. Wrapper usage follows reuse policy (no unnecessary wrappers).
9. Component class patterns align with `qa-test-tools/lokomokopom` guidance (component layer only).
10. Cached DOM artifacts under `.opencode/dom-cache/` are reused when relevant and not redundantly recollected.

Return:

- findings list (critical/high/medium/low),
- minimal fixes,
- exact validation commands:
  - `make verify-discovery`
  - `python -m pytest $TARGET_TEST_PATH -q --server-name=$SERVER_NAME`
