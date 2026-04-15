# E2E subagent: pom_builder

Input:

- SCENARIO_PROMPT: $SCENARIO_PROMPT
- TARGET_TEST_PATH: $TARGET_TEST_PATH

Task:

Use the `agent` tool once to implement only missing POM parts required by the scenario.

Rules:

1. Keep chain `page.section.component.method`.
2. Add locators only inside PO/components.
3. Add only used methods/components.
4. Public PO methods must have `@step(...)`.
5. Prefer extending existing pages/sections/components over adding new files.
6. For Component classes only, apply recommendations from `qa-test-tools/lokomokopom` when available.
7. Keep naming/style consistent with neighboring code.

Return:

- list of POM files changed,
- methods added,
- short rationale for each new method.
