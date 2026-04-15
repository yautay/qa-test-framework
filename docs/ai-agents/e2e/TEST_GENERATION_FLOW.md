# E2E Test Generation Flow

## Priority

This workflow applies **only to E2E tests**.

## Input contract

Agent input:

- `environment_url` or `server_name`
- `scenario_prompt` (business scenario description)
- optional: `suite_hint` (for example `netcorner/nuxt/pl`)

## Job workspace handoff

- Preferred mode: use a versioned job directory `work/e2e-jobs/<job_id>/`.
- Analysis pass writes artifacts in `analysis/` and status in `ticket.md`.
- Implementation pass must consume those artifacts and should not recollect DOM when cache is available.
- Start implementation only when ticket context is complete and analysis plan is present.

## Step 1: map runtime URL

- If `environment_url` is provided, execution should use `--base-url=<environment_url>`.
- If `server_name` is provided, execution should use `--server-name=<server_name>`.
- Test code must use `runtime_env.base_url` (no hardcoded hosts).

## Step 2: map scenario to suite and test file

- Preferred suite for this project: `qa/e2e/netcorner/nuxt/pl/tests/`.
- Choose the closest existing test module and style.
- Add a new file only when existing modules are not a thematic match.

## Step 3: map scenario steps to existing POM

- For each scenario step:
  - find existing `page.section.component.method`,
  - reuse it without duplication.
- Add missing elements minimally and locally.
- Reuse existing artifacts from `work/e2e-jobs/<job_id>/analysis/` before collecting DOM again.

## Step 4: extend POM (only when required)

- First, add a method to an existing component.
- Add a new class only when there is no reasonable existing location.
- Do not create objects unused by the test.
- Every new/changed public PO method should have `@step(...)` (Steps API).
- For Component classes only, follow `qa-test-tools/lokomokopom` recommendations when available.

## Step 5: test implementation

- Module marker: `pytestmark = [pytest.mark.e2e, ...]`.
- Business scenario marker: `@pytest.mark.scenario("...")`.
- Test data: use existing builders/generators when suitable.
- Assertions: clear, short, and diagnostic.

## Step 6: validation

- Run at minimum:
  - `make verify-discovery`
  - targeted test, for example `python -m pytest <test_path> -q`
- For marker/discovery changes, also run:
  - `make verify-scenarios` (if scenario catalog changes are involved)

## Definition of done

- Test passes locally on the selected environment URL.
- POM respects `page.section.component.method`.
- No unused PO classes/methods added "just in case".
- Changes are minimal and consistent with repo style.

## Run examples

```bash
python -m pytest qa/e2e/netcorner/nuxt/pl/tests/tests_account/test_create_account.py -q --server-name=demo
python -m pytest qa/e2e/netcorner/nuxt/pl/tests/tests_account/test_create_account.py -q --base-url=https://example.test
```
