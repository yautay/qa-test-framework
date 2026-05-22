---
name: new-test-suite-generate
description: Use when user wants to generate a coherent E2E test suite from multiple manual trace recording runs (trace.zip + checkpoints.json + metadata.json), including shared architecture, test data builders, and parametrization.
---

# New Test Suite Generate

Generate a coherent multi-scenario E2E test suite from multiple prepared recording sets.

## Inputs

- `suite_generation_payload` object from `new-test-suite-prepare`, or
- `suite_generation_payload_path` to JSON file from `new-test-suite-prepare`
- optional constraints:
  - desired test file names
  - preferred parametrization style
  - required marker set

When both object and path are provided, path is source of truth.

## User confirmation gate

Before any code changes, confirm with user (or apply explicit user-provided values) for:

- suite name (`suite_name`)
- marker set for the suite/tests
- allure severity policy (fixed value vs inherited local convention)
- suite file strategy (update existing file vs create new file)

If payload fields conflict with user preference, user preference is source of truth.

## Core rules

- Respect repository architecture and neighboring suite style.
- Keep host/domain environment-agnostic (no hardcoded base hosts).
- Assertions stay in tests only.
- No sleeps or `wait_for_timeout` stabilizers.
- No fallback/retry ladders in POM actions.
- Use timeout constants from project modules.
- Reuse existing flows/POMs/builders first; extend only where needed.

## AGENTS onboarding gate

Before implementation, mandatory:

1. Read `AGENTS.md` at repository root.
2. Resolve and read relevant nested `AGENTS.md` files for target domain/path:
   - `nuxt`: include guides under `qa/e2e/netcorner/nuxt/pl/**`.
   - `admin`: include guides under `qa/e2e/netcorner/admin/**`.
   - `mailhog`: include guides under `qa/e2e/netcorner/mailhog/**`.
   - `setup`: include setup-relevant guidance plus root rules.
   - `custom`: locate nearest `AGENTS.md` files on candidate paths and include root rules.

If root or relevant nested guides were not read, stop and return `needs-input` with missing paths.

## Implementation protocol

1. Load and validate suite payload (`schema_version`, required keys, source recording sets).
2. Confirm with user: suite name, markers, severity, and file strategy.
3. Build suite map from all payload scenarios.
4. Detect shared Arrange and shared flow fragments across scenarios.
5. Design one coherent architecture:
   - test module(s)
   - scenario case model (`case_id`, payload factory)
   - parametrization via `pytest.mark.parametrize(..., ids=lambda case: case.case_id)` when appropriate
   - shared builders/helpers with explicit typed data
6. Decide what to reuse vs extend in POM/flows/builders.
7. Implement tests in Arrange-Act-Assert shape with explicit business assertions per scenario.
8. Keep domain split strict: no business assertions in POM/flow methods.
9. Verify markers/imports/constants align with local conventions.

## Mandatory output sections

1. Suite architecture decisions
2. Files created/updated
3. Parametrization model (case object structure + ids strategy)
4. Shared test data/builder strategy
5. AGENTS context used (root + nested paths, key applied rules)
6. Verification commands to run
7. Remaining risks/follow-ups
