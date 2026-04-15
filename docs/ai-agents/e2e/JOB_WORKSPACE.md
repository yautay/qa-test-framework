# E2E Job Workspace

Use a versioned per-job workspace under `work/e2e-jobs/<job_id>/` to separate analysis and implementation passes.

## Why

- exploratory analysis can navigate multiple pages and collect findings,
- implementation can reuse collected data without repeating DOM collection,
- ticket status is explicit and auditable.

## Required files per job

- `ticket.md` - metadata, current status, and artifact links.
- `scenario.md` - source scenario prompt and constraints.
- `analysis/` - journey map, DOM inventory, locator gaps, open questions, implementation plan.
- `implementation/` - implementation notes and review output.

## Two-pass model

1. **Analysis pass**
   - run exploratory browsing,
   - collect DOM snapshots and notes,
   - generate questions and locator gap report,
   - ask follow-up questions in chat only when needed,
   - write/update ticket status to `analyzed` and list produced artifacts.
2. **Implementation pass**
   - starts only when analysis artifacts are present and ticket is ready,
   - uses analysis artifacts as input,
   - applies framework coding rules for E2E test generation.

Implementation commands should stop when ticket context is incomplete.
