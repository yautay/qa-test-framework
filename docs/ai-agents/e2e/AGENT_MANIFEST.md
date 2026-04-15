# E2E Agent Manifest

Goal: generate **E2E** tests aligned with the current framework architecture and coding style.

## Read Only This (in order)

1. `docs/ai-agents/e2e/POM_CONTRACT.md`
2. `docs/ai-agents/e2e/TEST_GENERATION_FLOW.md`
3. `docs/ai-agents/e2e/SELECTOR_AND_ASSERTION_RULES.md`
4. `docs/ai-agents/e2e/JOB_WORKSPACE.md`
5. `conftest.py` (CLI options: `--server-name`, `--base-url`, `--viewport`)
6. `qa/conftest.py` (runtime env, base_url, target resolution, reporting payload)
7. `qa/e2e/conftest.py` (Playwright lifecycle: `browser/context/page`)
8. `qa/e2e/netcorner/nuxt/pl/conftest.py` (suite-level runtime_env)
9. `framework/base/page_objects/base_page.py`
10. `framework/base/page_objects/base_component.py`
11. `qa/e2e/netcorner/nuxt/pl/lib/page_objects/` (pages/sections/components/overlays)
12. `qa/e2e/netcorner/nuxt/pl/lib/flows/`
13. `qa/e2e/netcorner/nuxt/pl/tests/`
14. `framework/targeting/registry.py` + `framework/targeting/resolver.py`
15. `docs/FIXTURES.md`

## Scope rules (hard)

- Focus: only **E2E** tests (`qa/e2e/`).
- Do not change CI config (`.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile`) without explicit request.
- Do not refactor beyond scenario scope.
- Do not create new POM objects "just in case".
- Do not model a full page if the test uses only 1-2 elements.
- In job workspace mode, implementation pass must consume `work/e2e-jobs/<job_id>/analysis/` outputs.

## POM rules (hard)

- Every test step must go through: `page.section.component.method`.
- No direct `page.locator(...)` in test files.
- No UI selectors or UI interaction logic in tests; keep them in `components`.
- Create only classes/methods used by the current scenario.
- Public Page Object methods (`pages/sections/components/overlays`) must use Steps API via `@step(...)`, consistent with repo style.
- For **Component class construction only**, follow recommendations from `qa-test-tools/lokomokopom` when available.

## Runtime rules (hard)

- The environment URL must be resolved by runtime (`runtime_env.base_url`).
- Allowed run modes:
  - `--server-name=<alias|dns>`
  - `--base-url=https://...` (explicit override)
- Do not hardcode target URLs in test code.

## Expected output from agent

- Minimum required changes to run the scenario.
- Test placed in the correct directory `qa/e2e/.../tests/...`.
- POM methods/components added only where used.
- Preserved repository style and conventions.
