---
name: new-test-suite-prepare
description: Use when user wants research/planning from multiple recording sets before generating a coherent parametrized E2E suite.
---

# New Test Suite Prepare

Prepare deterministic research output for multi-scenario suite generation.

## Inputs

- `suite_name`
- `target_domain` (`nuxt|admin|mailhog|setup|custom`)
- `recording_sets` (array):
  - `scenario_name`
  - `trace_zip_path`
  - `checkpoints_json_path`
  - optional `metadata_json_path`

## Core rules

- Do not generate final test code.
- Keep host/domain environment-agnostic; do not hardcode base URLs.
- Assertions in tests, not in page objects.
- No sleeps/wait_for_timeout stabilizers.
- Use timeout constants (no raw timeout integers).
- Avoid fallback/retry ladders in POM actions.

## AGENTS onboarding gate

Before analysis, mandatory:

1. Read `AGENTS.md` at repository root.
2. Read relevant nested `AGENTS.md` files for target domain/path.
3. If missing, stop with `needs-input`.

## Deterministic output and persistence

- Always return output in exactly the same section order defined below.
- Always produce a machine-readable payload JSON object named `suite_generation_payload`.
- Always save payload to file before final response:
  - default directory: `thoughts/ai_gen/prepared/`
  - filename: `<timestamp_utc>_<suite_name>_suite_generation_payload.json`
- If user provides explicit output path, use it.
- Include `payload_file_path` in final response.

## Mandatory output sections

1. `status`
2. `suite_summary`
3. `candidate_file_map`
4. `proposed_files`
5. `suite_blueprint` (arrange -> act -> assert)
6. `parametrization_strategy`
7. `shared_builder_strategy`
8. `risks_and_mitigations`
9. `agents_context_used`
10. `suite_generation_payload`
11. `payload_file_path`

`suite_generation_payload` must contain:

- `schema_version` (string, fixed: `"1.0"`)
- `prepared_at_utc`
- `suite_name`
- `target_domain`
- `source_recording_sets`
- `markers`
- `case_model`
- `data_requirements`
- `required_page_objects`
- `assertions_matrix`
- `open_questions`
- `agents_context_used`
