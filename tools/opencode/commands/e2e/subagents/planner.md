# E2E subagent: planner

Input:

- SERVER_NAME: $SERVER_NAME
- SCENARIO_PROMPT: $SCENARIO_PROMPT

Task:

Use the `agent` tool once as a planning sub-task and return only a concrete implementation plan.

Plan must include:

1. target test module path (`qa/e2e/.../tests/...`),
2. existing POM methods to reuse,
3. missing POM methods/components to add (minimal set only),
4. whether wrapper is needed or not, with justification,
5. expected markers and parametrize shape,
6. validation commands.

Constraints:

- E2E only.
- POM chain `page.section.component.method`.
- no hardcoded URLs, use `--server-name=$SERVER_NAME`.
- no PO objects created "for future".
