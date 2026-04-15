# E2E job: init ticket

Input:

- JOB_ID: $JOB_ID
- JOB_TITLE: $JOB_TITLE
- SERVER_NAME: $SERVER_NAME
- SCENARIO_PROMPT: $SCENARIO_PROMPT
- SEED_PATHS: $SEED_PATHS

Task:

1. Create a job workspace in `work/e2e-jobs/<job_id>/`.
2. If any required data is missing, ask short follow-up questions in chat and fill it before writing files.
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
5. Return created paths and exact next command: `project:e2e:job:analyze`.

Rules:

- Keep it simple and interactive.
- Do not run Python helper scripts for this flow.
- Do not implement tests in this command.
