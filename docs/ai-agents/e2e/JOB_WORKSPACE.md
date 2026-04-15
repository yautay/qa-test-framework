# E2E Job Workspace

Use a versioned per-job workspace under `work/e2e-jobs/<job_id>/` to separate analysis and implementation passes.

## Why

- exploratory analysis can navigate multiple pages and collect findings,
- implementation can reuse collected data without repeating DOM collection,
- handoff status is explicit and auditable.

## Required files per job

- `job.json` - metadata and current status.
- `scenario.md` - source scenario prompt and constraints.
- `analysis/` - journey map, open questions, locator gaps, refined contract.
- `handoff/analysis_contract.json` - handoff status between passes.
- `implementation/` - implementation notes and review output.

## Two-pass model

1. **Analysis pass**
   - run exploratory browsing,
   - collect DOM snapshots and notes,
   - generate questions and locator gap report,
   - ask follow-up questions in chat and persist user answers,
   - set handoff to `needs_user_answers`.
2. **Implementation pass**
   - starts only when handoff is `ready_for_implementation`,
   - uses analysis artifacts as input,
   - applies framework coding rules for E2E test generation.

## Handoff contract

`handoff/analysis_contract.json` must include:

- `status` (`draft`, `needs_user_answers`, `ready_for_implementation`),
- `ready_for_implementation` (boolean),
- `analysis_outputs` (paths to analysis artifacts),
- `updated_at_utc`.

Implementation commands should stop when handoff is not ready.
