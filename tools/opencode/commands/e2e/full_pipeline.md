# E2E full pipeline (planner -> implement -> review)

Input:

- SERVER_NAME: $SERVER_NAME
- SCENARIO_PROMPT: $SCENARIO_PROMPT
- JOB_ID: $JOB_ID

Task:

1. Initialize and analyze job workspace:
   - `project:e2e:job:init`
   - `project:e2e:job:analyze`
2. Ask user to answer open questions and finalize handoff:
   - `project:e2e:job:finalize_analysis`
3. Implement test and minimal POM changes:
   - `project:e2e:job:implement`
4. Run review pass:
   - `project:e2e:job:review`
5. Apply necessary fixes and re-run validation commands.

Hard constraints:

- E2E only.
- URL by runtime selector `--server-name=$SERVER_NAME`.
- reuse cached analysis artifacts from `work/e2e-jobs/$JOB_ID/analysis/` when available.
- POM chain `page.section.component.method`.
- Steps API in public PO methods.
- Component class patterns aligned with `qa-test-tools/lokomokopom` guidance.
- no unused PO objects.
- wrappers only for reusable complex flows.

Validation commands:

- `make verify-discovery`
- `python -m pytest <new_or_updated_test_path> -q --server-name=$SERVER_NAME`

Return:

- final changed files,
- what was reused vs newly added,
- review findings and fixes,
- validation output summary.
