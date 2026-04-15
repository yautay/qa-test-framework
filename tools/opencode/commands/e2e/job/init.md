# E2E job: init workspace

Input:

- JOB_ID: $JOB_ID
- JOB_TITLE: $JOB_TITLE
- SERVER_NAME: $SERVER_NAME
- SCENARIO_PROMPT: $SCENARIO_PROMPT
- SEED_PATHS: $SEED_PATHS

Task:

1. Initialize a versioned per-job workspace:
   - `python tools/opencode/job_init.py --job-id=$JOB_ID --title "$JOB_TITLE" --server-name=$SERVER_NAME --scenario "$SCENARIO_PROMPT" --seed-paths-csv "$SEED_PATHS"`
2. Verify that `seed_paths` in `job.json` matches intended exploration paths.
3. Show generated file paths and explain next command.

Rules:

- Keep scenario text in `work/e2e-jobs/$JOB_ID/scenario.md`.
- Do not implement tests in this command.
