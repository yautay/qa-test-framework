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

## Deterministic output and persistence

- Always return output in exactly the same section order defined below.
- Always produce a machine-readable payload JSON object named `generation_payload`.
- Always save `generation_payload` to file before final response:
  - default directory: `artifacts/ai-test-tools/prepared/`
  - filename: `<timestamp_utc>_<scenario_name>_generation_payload.json`
- If user provides explicit output path, use it instead.
- In final response, include `payload_file_path` (absolute or workspace-relative path).

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

1. Read `AGENTS.md` at repository root.
2. Resolve and read relevant nested `AGENTS.md` files for the inferred target path/domain before analysis:
   - `nuxt`: include guides under `qa/e2e/netcorner/nuxt/pl/**`.
   - `admin`: include guides under `qa/e2e/netcorner/admin/**`.
   - `mailhog`: include guides under `qa/e2e/netcorner/mailhog/**`.
   - `setup`: include setup-relevant guidance plus root rules.
   - `custom`: locate nearest `AGENTS.md` files on the candidate path and include root rules.
3. Discover nearby tests, POMs, flows, and test data in relevant domain.
4. Reconstruct deterministic flow steps from checkpoints + trace context.
5. Propose locator strategy for each key checkpoint.
6. Define Arrange-Act-Assert blueprint.
7. Propose markers and test placement path.
8. Return generation-ready payload.

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
8. `agents_context_used`:
   - `root_agents_path`
   - `nested_agents_paths`
   - `applied_rules` (3-6 concise bullets)
9. `generation_payload` (single JSON block)
10. `payload_file_path`

## Output template (strict)

Use this exact top-level order in final response:

1. `status`
2. `scenario_summary`
3. `candidate_file_map`
4. `proposed_files`
5. `test_blueprint`
6. `locator_strategy`
7. `risks_and_mitigations`
8. `agents_context_used`
9. `generation_payload`
10. `payload_file_path`

`generation_payload` must contain:

- `schema_version` (string, fixed: `"1.0"`)
- `prepared_at_utc`
- `source_artifacts` (`trace_zip_path`, `checkpoints_json_path`, optional `metadata_json_path`)
- `test_name`
- `target_domain`
- `markers`
- `data_requirements`
- `required_page_objects`
- `assertions_list`
- `open_questions`
- `agents_context_used`

## Output quality gate

Set status:

- `ready` when trace/checkpoints provide deterministic assertions.
- `needs-input` when critical steps/assertion anchors are missing.
- `needs-input` when root `AGENTS.md` or relevant nested `AGENTS.md` files were not read.
- `needs-input` when payload file could not be written.
