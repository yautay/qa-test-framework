# E2E Jobs Workspace

This directory stores per-job workspaces used by OpenCode commands.

## Layout

- `work/e2e-jobs/<job_id>/ticket.md` - source of truth for job state
- `work/e2e-jobs/<job_id>/scenario.md` - scenario prompt copy
- `work/e2e-jobs/<job_id>/analysis/` - analysis notes, DOM findings, plan
- `work/e2e-jobs/<job_id>/implementation/` - implementation notes and review notes

## Workflow

1. `project:e2e:job:init` - create ticket/job and collect missing details in chat.
2. `project:e2e:job:analyze` - run analysis + DOM scraping + implementation plan.
3. `project:e2e:job:implement` - implement changes in framework code using job context.

## Important rule

If analysis or implementation creates separate artifacts, they must be referenced in `ticket.md`.

## Heavy artifacts

- Large cached artifacts should be written under `analysis/cache/`.
- The local `.gitignore` in this directory ignores those heavy files.
