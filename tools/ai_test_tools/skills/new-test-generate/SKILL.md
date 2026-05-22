---
name: new-test-generate
description: Use when user wants to generate final E2E test implementation from the prepared payload produced by new-test-prepare.
---

# New Test Generate

Generate final E2E test code using prepared payload from `new-test-prepare`.

## Inputs

- `generation_payload` from prepare stage
- optional constraints (file names, parametrization preferences)

## Core rules

- Respect repository test architecture and neighboring suite style.
- Keep host/domain environment-agnostic (no hardcoded base hosts).
- Assertions remain in tests; page objects expose actions/reads only.
- No sleeps/wait_for_timeout stabilizers.
- No hidden retry/fallback ladders in POM actions.
- Use timeout constants from project modules.
- Reuse existing flows/POMs/builders first; extend only where needed.

## Implementation protocol

1. Resolve target test location and marker conventions.
2. Implement or extend required test data builders.
3. Implement/extend POM reads/actions only when missing.
4. Create test in Arrange-Act-Assert structure.
5. Add explicit business assertions from payload.
6. Verify imports/constants/markers follow local standards.

## Mandatory output sections

1. Files created/updated
2. Rationale for key implementation decisions
3. Verification commands to run
4. Any remaining risks or follow-up tasks
