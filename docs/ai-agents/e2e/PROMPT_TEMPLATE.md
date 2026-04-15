# Prompt Template For E2E Generator Agent

Use this template when you want to generate a new E2E test.

```text
Task: generate an E2E test in this repository.

Input:
- environment_url: <https://...> or empty
- server_name: <demo|prod|local|dns-host> or empty
- scenario_prompt: <scenario description>
- suite_hint: <for example netcorner/nuxt/pl>
- job_id: <optional job id under work/e2e-jobs>

Hard requirements:
1) Focus only on E2E (`qa/e2e`).
2) Use POM only in this scheme: `page.section.component.method`.
3) Do not create unused POs, sections, or components.
4) Do not hardcode URLs in tests. Use `runtime_env.base_url`.
5) Preserve current pytest style, markers, and naming.
6) Decorate public PO methods with `@step(...)` (Steps API), consistent with current code.
7) For Component classes only, apply recommendations from `qa-test-tools/lokomokopom`.
8) If `job_id` is provided, use artifacts from `work/e2e-jobs/<job_id>/analysis/` and enforce handoff readiness.

Work steps:
- First read `docs/ai-agents/e2e/AGENT_MANIFEST.md`.
- Map the scenario to existing page objects.
- Add only missing methods/selectors.
- Add the test to the appropriate module in `qa/e2e/.../tests/`.

Expected output:
- list of changed files,
- short rationale per change,
- validation commands (`make verify-discovery` + targeted pytest).
```
