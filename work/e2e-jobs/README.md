# E2E Jobs Workspace

This directory stores versioned, per-job workspaces for the two-pass E2E flow:

1. analysis pass (exploratory browsing, DOM cache, questions, locator gaps),
2. implementation pass (test and POM code changes in this framework).

## Layout

- `work/e2e-jobs/<job_id>/job.json`
- `work/e2e-jobs/<job_id>/scenario.md`
- `work/e2e-jobs/<job_id>/analysis/`
- `work/e2e-jobs/<job_id>/handoff/analysis_contract.json`
- `work/e2e-jobs/<job_id>/implementation/`

## Handoff model

- The implementation pass must use files from `analysis/` and `handoff/`.
- `handoff/analysis_contract.json` is the source of truth for status.
- Implementation starts only when status is `ready_for_implementation`.
- Users answer follow-up questions in chat; the agent persists them into `analysis/answers.md` automatically.

## Heavy artifacts

- Large cached artifacts are written into `analysis/cache/`.
- The local `.gitignore` in this directory ignores those heavy files.
