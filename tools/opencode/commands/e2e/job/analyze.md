# E2E job: exploratory analysis

Input:

- JOB_ID: $JOB_ID
- EXTRA_PATHS: $EXTRA_PATHS

Task:

1. Run exploratory analysis for this job:
   - `python tools/opencode/job_analyze.py --job-id=$JOB_ID`
2. If `EXTRA_PATHS` is provided, include them by rerunning with repeated `--path` values.
   - `python tools/opencode/job_analyze.py --job-id=$JOB_ID --paths-csv "$EXTRA_PATHS"`
3. Review generated files:
   - `analysis/journey_map.md`
   - `analysis/locator_gaps.md`
   - `analysis/open_questions.md`
   - `analysis/refined_behavior_contract.md`
   - `handoff/analysis_contract.json`
4. Ask the user focused follow-up questions from `analysis/open_questions.md` **in chat during this job**.
5. Persist answers automatically and finalize handoff in the same run:
   - write/update `work/e2e-jobs/$JOB_ID/analysis/answers.md`
   - run `python tools/opencode/job_finalize_analysis.py --job-id=$JOB_ID`
6. If answers are still incomplete, keep handoff in `needs_user_answers` and clearly state what is missing.

Rules:

- Analysis only; no implementation in this command.
- Explicitly call out missing stable locators for product-side improvements.
- Keep findings scoped to E2E behavior.
- The user should not be asked to manually edit files unless explicitly requested.
