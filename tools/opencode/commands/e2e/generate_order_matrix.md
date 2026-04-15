# Generate E2E order matrix test

Input:

- SERVER_NAME: $SERVER_NAME
- SCENARIO_PROMPT: $SCENARIO_PROMPT
- JOB_ID: $JOB_ID
- LISTING_PATH_HINT: $LISTING_PATH_HINT
- DELIVERY_VARIANTS: $DELIVERY_VARIANTS
- PAYMENT_VARIANTS: $PAYMENT_VARIANTS

Goal:

Create E2E test coverage for checkout matrix (delivery x payment) using existing framework style.

Hard rules:

1. E2E only (`qa/e2e/` scope).
2. Runtime URL from `--server-name=$SERVER_NAME`, never hardcode environment URL.
3. Reuse analysis artifacts under `work/e2e-jobs/$JOB_ID/analysis/` when `JOB_ID` is provided.
4. Otherwise reuse DOM cache under `.opencode/dom-cache/**/latest/` when available.
5. Keep POM chain `page.section.component.method`.
6. Keep Steps API in public PO methods (`@step(...)`).
7. Reuse existing wrappers/flows before adding new ones:
   - `ClientWrappers` for client lifecycle.
8. Add/extend wrapper only for truly reusable multi-step cross-page flows.
9. For Component classes only, apply recommendations from `qa-test-tools/lokomokopom` when available.
10. Do not add unused PO objects.

Implementation guidance:

- Parse `DELIVERY_VARIANTS` and `PAYMENT_VARIANTS` as matrix cases for `pytest.mark.parametrize`.
- Place test in orders suite under `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/`.
- If listing entry is needed, prefer existing listing helpers and minimal PO extension.
- Assertions should be clear and business-level for each matrix case.

Validation:

1. `make verify-discovery`
2. `python -m pytest <new_orders_test_path> -q --server-name=$SERVER_NAME`

Return:

- generated/updated files,
- matrix case IDs,
- validation results.
