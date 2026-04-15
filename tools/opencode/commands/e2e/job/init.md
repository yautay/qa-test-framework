# E2E job: init ticket

Input:

- Use natural language only (no env vars).
- Collect all required fields interactively in chat during init.

Task:

1. Ask the user for required data in chat (job id or title, server, scenario, optional seed paths).
2. Create a job workspace in `work/e2e-jobs/<job_id>/`.
3. Create/update:
   - `work/e2e-jobs/<job_id>/ticket.md` (source of truth)
   - `work/e2e-jobs/<job_id>/scenario.md` (raw scenario copy)
   - `work/e2e-jobs/<job_id>/analysis/`
   - `work/e2e-jobs/<job_id>/implementation/`
4. In `ticket.md` include at minimum:
   - job metadata (`job_id`, title, server, created/updated date),
   - scenario scope,
   - seed paths,
   - status set to `new`,
   - empty sections for `Artifacts`, `Open Questions`, and `Implementation Notes`.
5. Return created paths and exact next command invocation with ticket context.

Rules:

- Keep it simple and interactive.
- No env-var style input contract.
- Do not implement tests in this command.
