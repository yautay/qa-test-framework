# E2E job: implement

Input:

- Ticket context from init/analyze in chat (prefer `job_id`).

Task:

1. Resolve job id from provided ticket context; if ambiguous, ask one short question.
2. Read ticket context and analysis artifacts:
   - `work/e2e-jobs/<job_id>/ticket.md`
   - `work/e2e-jobs/<job_id>/scenario.md`
   - `work/e2e-jobs/<job_id>/analysis/implementation_plan.md`
   - `work/e2e-jobs/<job_id>/analysis/locator_gaps.md`
3. If key inputs are missing, ask targeted questions in chat before coding.
4. Implement test and minimal POM/framework changes in repo code.
5. Follow framework rules:
   - E2E only
   - runtime URL resolution via `--server-name`
   - `page.section.component.method`
   - `@step(...)` in public PO methods
   - wrappers only for reusable complex flows
6. Save implementation notes to:
   - `work/e2e-jobs/<job_id>/implementation/implementation_notes.md`
7. Update `ticket.md` and include:
   - status set to `implemented`,
   - changed code files,
   - validation commands run and outcomes,
   - remaining risks or follow-ups.

Validation:

- `make verify-discovery`
- `python -m pytest <new_or_updated_test_path> -q --server-name=<server_name_from_ticket>`

Rules:

- No env-var style input contract.
