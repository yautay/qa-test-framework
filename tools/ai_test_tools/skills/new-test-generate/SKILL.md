---
name: new-test-generate
description: Use when user wants to generate final E2E test implementation from the prepared payload produced by new-test-prepare.
---

# New Test Generate

Generate final E2E test code using prepared payload from `new-test-prepare`.

## Inputs

- `generation_payload` from prepare stage, or
- `generation_payload_path` pointing to JSON file produced by prepare stage
- optional constraints (file names, parametrization preferences)

When both payload object and path are provided, path is source of truth.

## User confirmation gate

Before any code changes, confirm with user (or apply explicit user-provided values) for:

- test name (`test_name`)
- marker set (`pytestmark`/scenario marker plan)
- allure severity (or "keep existing convention" when not used nearby)
- target file path (create new vs update existing)

If payload fields conflict with user preference, user preference is source of truth.

## Core rules

- Respect repository test architecture and neighboring suite style.
- Keep host/domain environment-agnostic (no hardcoded base hosts).
- Assertions remain in tests; page objects expose actions/reads only.
- No sleeps/wait_for_timeout stabilizers.
- No hidden retry/fallback ladders in POM actions.
- Use timeout constants from project modules.
- Reuse existing flows/POMs/builders first; extend only where needed.

## Implementation protocol

1. Read `AGENTS.md` at repository root.
2. Resolve and read relevant nested `AGENTS.md` files for target domain/path before implementation:
   - `nuxt`: include guides under `qa/e2e/netcorner/nuxt/pl/**`.
   - `admin`: include guides under `qa/e2e/netcorner/admin/**`.
   - `mailhog`: include guides under `qa/e2e/netcorner/mailhog/**`.
   - `setup`: include setup-relevant guidance plus root rules.
   - `custom`: locate nearest `AGENTS.md` files on the candidate path and include root rules.
3. Load and validate `generation_payload` (schema version, required keys, artifact references).
4. Confirm with user: test name, markers, severity, and target file path.
5. Resolve target test location and marker conventions.
6. Implement or extend required test data builders.
7. Implement/extend POM reads/actions only when missing.
8. Create test in Arrange-Act-Assert structure.
9. Add explicit business assertions from payload.
10. Verify imports/constants/markers follow local standards.

## Mandatory output sections

1. Files created/updated
2. Rationale for key implementation decisions
3. AGENTS context used (root + nested paths, plus key applied rules)
4. Verification commands to run
5. Any remaining risks or follow-up tasks

## Output quality gate

- If root `AGENTS.md` or relevant nested `AGENTS.md` files were not read, stop and return `needs-input` with missing guide paths.
