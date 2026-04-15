# E2E job: finalize analysis handoff

Input:

- JOB_ID: $JOB_ID
- ANSWERS_TEXT: $ANSWERS_TEXT

Task:

1. Finalize handoff status using inline answers from chat when provided:
   - `python tools/opencode/job_finalize_analysis.py --job-id=$JOB_ID --answers-text "$ANSWERS_TEXT"`
2. If `ANSWERS_TEXT` is empty, use existing `analysis/answers.md` content.
3. Show final handoff state from:
   - `work/e2e-jobs/$JOB_ID/handoff/analysis_contract.json`

Rules:

- Do not implement tests in this command.
- Implementation can start only after status becomes `ready_for_implementation`.
