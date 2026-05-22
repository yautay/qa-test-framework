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

## Live verification and debugging gate

- During implementation, do not stop at static code generation; verify behavior on a live run.
- Mandatory validation loop for each affected scenario:
  1. run focused pytest (single file/case or marker subset),
  2. analyze first failure,
  3. verify live DOM/locator behavior (visibility/count/text) when failure suggests selector/readiness mismatch,
  4. apply minimal contract-safe fix,
  5. re-run focused pytest until stable.
- For selector issues, prefer semantically stable locators and visibility scoping (`:visible`, role-based locators, root-scoped locators) over brittle CSS chains.
- If text is present but assertion fails, explicitly check strict-mode collisions (multiple matches) and narrow locator intent instead of adding retries.
- No "paper fixes": do not finish with "should work" without at least one executed verification command result.
- If live verification cannot be executed (e.g. no VPN/env access), return `needs-input` with exact blocker and the precise command/check list required from user.

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
11. Execute live validation loop (focused pytest + selector/DOM checks when needed) and finalize only after pass or explicit environment blocker.

## Mandatory output sections

1. Files created/updated
2. Rationale for key implementation decisions
3. AGENTS context used (root + nested paths, plus key applied rules)
4. Verification commands to run
5. Any remaining risks or follow-up tasks

Verification section must include:
- commands actually executed,
- pass/fail outcome,
- for failures: diagnosed root cause and what was changed.

## Output quality gate

- If root `AGENTS.md` or relevant nested `AGENTS.md` files were not read, stop and return `needs-input` with missing guide paths.
