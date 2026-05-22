---
name: new-test-prepare
description: Use when user asks to prepare a new E2E automated test from Playwright trace artifacts (trace.zip, checkpoints.json, metadata.json) before writing final test code.
---

# New Test Prepare

Prepare implementation blueprint for a NEW E2E test in this repository from manual trace artifacts.

## Inputs

- `scenario_name` (human-readable)
- `target_domain` (`nuxt|admin|mailhog|setup|custom`)
- `trace_zip_path`
- `checkpoints_json_path`
- optional: screenshots dir, notes, expected outcomes

## Core rules

- Do not generate final test code.
- Keep host/domain environment-agnostic.
- Do not hardcode base URLs.
- Reason mostly on route/path suffixes and business intent.
- Follow repository contract:
  - Assertions in tests, not in page objects.
  - No sleeps or wait_for_timeout stabilizers.
  - Use existing POM/flows/builders where possible.
  - Use timeout constants (no raw timeout integers).
  - Avoid fallback/retry ladders in POM actions.

## Execution protocol

1. Discover nearby tests, POMs, flows, and test data in relevant domain.
2. Reconstruct deterministic flow steps from checkpoints + trace context.
3. Propose locator strategy for each key checkpoint.
4. Define Arrange-Act-Assert blueprint.
5. Propose markers and test placement path.
6. Return generation-ready payload.

## Mandatory output sections

1. Scenario summary
2. Candidate file map
3. Proposed new or updated files (paths only)
4. Step-by-step test blueprint (arrange -> act -> assert)
5. Locator strategy table
6. Risks and mitigations
7. Ready-for-generation payload:
   - `test_name`
   - `target_domain`
   - `markers`
   - `data_requirements`
   - `required_page_objects`
   - `assertions_list`
   - `open_questions`

## Output quality gate

Set status:

- `ready` when trace/checkpoints provide deterministic assertions.
- `needs-input` when critical steps/assertion anchors are missing.
