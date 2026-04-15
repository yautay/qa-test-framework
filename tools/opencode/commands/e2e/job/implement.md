# E2E job: implement

Input:

- JOB_ID: $JOB_ID

Task:

1. Read ticket context and analysis artifacts:
   - `work/e2e-jobs/$JOB_ID/ticket.md`
   - `work/e2e-jobs/$JOB_ID/scenario.md`
   - `work/e2e-jobs/$JOB_ID/analysis/implementation_plan.md`
   - `work/e2e-jobs/$JOB_ID/analysis/locator_gaps.md`
2. If key inputs are missing, ask targeted questions in chat before coding.
3. Implement test and minimal POM/framework changes in repo code.
4. Follow framework rules:
   - E2E only
   - runtime URL resolution via `--server-name`
   - `page.section.component.method`
   - `@step(...)` in public PO methods
   - wrappers only for reusable complex flows
5. Save implementation notes to:
   - `work/e2e-jobs/$JOB_ID/implementation/implementation_notes.md`
6. Update `ticket.md` and include:
   - status set to `implemented`,
   - changed code files,
   - validation commands run and outcomes,
   - remaining risks or follow-ups.

Validation:

- `make verify-discovery`
- `python -m pytest <new_or_updated_test_path> -q --server-name=<server_name_from_ticket>`
