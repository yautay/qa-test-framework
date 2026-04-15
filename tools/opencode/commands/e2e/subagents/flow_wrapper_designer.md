# E2E subagent: flow_wrapper_designer

Input:

- SCENARIO_PROMPT: $SCENARIO_PROMPT
- TARGET_TEST_PATH: $TARGET_TEST_PATH

Task:

Use the `agent` tool once and decide if wrapper/flow should be added.

Wrapper decision policy:

- Add wrapper only if flow is:
  - multi-step,
  - cross-page or cross-component,
  - expected to be reused across tests.
- If flow is single-use/simple, keep logic in test + POM methods (no new wrapper).

When wrapper is needed:

1. Extend existing wrapper class first (for example `ClientWrappers`) if it matches domain.
2. Keep wrapper methods as business tasks (not low-level locator operations).
3. Reuse existing PO methods, do not duplicate UI logic.

Return:

- wrapper decision (yes/no),
- affected wrapper files,
- methods to add/change.
