# E2E job: implement from handoff

Input:

- JOB_ID: $JOB_ID

Task:

1. Read and validate handoff status from:
   - `work/e2e-jobs/$JOB_ID/handoff/analysis_contract.json`
2. If status is not `ready_for_implementation`, stop and explain what is missing.
3. Implement tests and minimal required POM changes using job artifacts:
   - `work/e2e-jobs/$JOB_ID/scenario.md`
   - `work/e2e-jobs/$JOB_ID/analysis/refined_behavior_contract.md`
   - `work/e2e-jobs/$JOB_ID/analysis/locator_gaps.md`
   - `work/e2e-jobs/$JOB_ID/analysis/dom_inventory.json`
4. Follow framework rules:
   - E2E only
   - runtime URL resolution via `--server-name`
   - `page.section.component.method`
   - `@step(...)` in public PO methods
   - wrappers only for reusable complex flows
   - component class guidance from `qa-test-tools/lokomokopom` (component layer only)
5. Save implementation notes to:
   - `work/e2e-jobs/$JOB_ID/implementation/implementation_notes.md`

Validation:

- `make verify-discovery`
- `python -m pytest <new_or_updated_test_path> -q --server-name=<server_name_from_job>`
