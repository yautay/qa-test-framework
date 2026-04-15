# E2E job: analyze and plan

Input:

- Ticket context from init command (prefer `job_id` in chat text).
- Optional extra exploration paths provided in chat (no env vars).

Task:

1. Resolve job id from provided ticket context; if ambiguous, ask one short question.
2. Read `work/e2e-jobs/<job_id>/ticket.md` and `scenario.md`.
3. If user provided extra paths in chat, include them in analysis scope.
4. Perform analysis for scenario scope, including DOM scraping for relevant pages.
5. Save analysis artifacts under `work/e2e-jobs/<job_id>/analysis/`, at minimum:
   - `journey_map.md`
   - `dom_inventory.md`
   - `locator_gaps.md`
   - `open_questions.md`
   - `implementation_plan.md`
6. Ask focused follow-up questions in chat only when truly needed.
7. Update `ticket.md` and explicitly list:
   - current status set to `analyzed`,
   - all created analysis artifacts,
   - open questions and known assumptions,
   - implementation plan summary.

Rules:

- Analysis only; no code implementation in this command.
- Keep findings scoped to E2E behavior and framework constraints.
- Any artifact saved outside `ticket.md` must be referenced in `ticket.md`.
- No env-var style input contract.
