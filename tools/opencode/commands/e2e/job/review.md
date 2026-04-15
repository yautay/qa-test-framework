# E2E job: review implementation

Input:

- JOB_ID: $JOB_ID
- TARGET_TEST_PATH: $TARGET_TEST_PATH

Task:

1. Review implementation against job handoff artifacts.
2. Verify compliance:
   - E2E scope only
   - `page.section.component.method`
   - no direct selectors in tests
   - `@step(...)` on public PO methods
   - no unused PO additions
   - wrapper usage policy respected
   - component class guidance from `qa-test-tools/lokomokopom` applied where relevant
3. Update review notes in:
   - `work/e2e-jobs/$JOB_ID/implementation/review.md`
4. Run validation commands:
   - `make verify-discovery`
   - `python -m pytest $TARGET_TEST_PATH -q --server-name=<server_name_from_job>`

Return:

- prioritized findings,
- fixes applied,
- validation status.
