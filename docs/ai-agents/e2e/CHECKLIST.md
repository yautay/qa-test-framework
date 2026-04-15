# E2E Generation Checklist

## Before coding

- [ ] Does the scenario belong to E2E (not API/visual/ASO)?
- [ ] Is the correct suite selected (`qa/e2e/...`)?
- [ ] Is environment URL routing handled via `--server-name` or `--base-url`?
- [ ] Did the agent check existing page/section/component methods before adding new ones?
- [ ] If job workspace mode is used, is `ticket.md` complete and status ready for implementation?

## During coding

- [ ] Every test step goes through `page.section.component.method`.
- [ ] No `page.locator(...)` or selectors in test files.
- [ ] Only actually used POM elements are added.
- [ ] Public PO methods use `@step(...)` (Steps API) in repo style.
- [ ] Markers are preserved (`pytestmark`, `@pytest.mark.scenario(...)`).
- [ ] Import and naming style matches neighboring files.
- [ ] Analysis artifacts from `work/e2e-jobs/<job_id>/analysis/` are reused when available.

## After coding

- [ ] `make verify-discovery` was executed.
- [ ] Targeted test was executed: `python -m pytest <new_test> -q`.
- [ ] No changes outside required scope.
- [ ] No changes to CI or unrelated configuration.

## Review gate

- [ ] Is the new test readable and aligned with the business prompt?
- [ ] Were no unused PO classes/methods introduced?
- [ ] Are assertions explicit and diagnostic?
