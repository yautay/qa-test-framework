# E2E job: analyze and plan

Input:

- JOB_ID: $JOB_ID
- EXTRA_PATHS: $EXTRA_PATHS

Task:

1. Read `work/e2e-jobs/$JOB_ID/ticket.md` and `scenario.md`.
2. Perform analysis for scenario scope, including DOM scraping for relevant pages.
3. Save analysis artifacts under `work/e2e-jobs/$JOB_ID/analysis/`, at minimum:
   - `journey_map.md`
   - `dom_inventory.md`
   - `locator_gaps.md`
   - `open_questions.md`
   - `implementation_plan.md`
4. If `EXTRA_PATHS` is provided, include those paths in analysis.
5. Ask focused follow-up questions in chat only when truly needed.
6. Update `ticket.md` and explicitly list:
   - current status set to `analyzed`,
   - all created analysis artifacts,
   - open questions and known assumptions,
   - implementation plan summary.

Rules:

- Analysis only; no code implementation in this command.
- Keep findings scoped to E2E behavior and framework constraints.
- Any artifact saved outside `ticket.md` must be referenced in `ticket.md`.
- Do not run Python helper scripts for this flow.
