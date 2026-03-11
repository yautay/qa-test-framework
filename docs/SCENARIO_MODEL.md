# Scenario model (code-driven)

Smoke checkout scenarios are defined in code and validated automatically.

## Source of truth

- Scenario definitions: `qa/e2e/netcorner/nuxt/pl/app/data/scenario_catalog.py`
- Scenario case data: `qa/e2e/netcorner/nuxt/pl/app/data/orders_smoke_data.py`
- Full-process runner: `qa/e2e/netcorner/nuxt/pl/tests/test_orders_smoke_full_process.py`

## What is validated

`tools/scenarios/verify_scenarios.py` verifies:
- axis coverage (`order_as`, `delivery_kind`, `payment_kind`),
- duplicated scenario IDs,
- scenario-to-test mapping for full-process smoke cases.

## Optional method-level scenario description

Each pytest test method can include optional business description:

```python
from qa.scenario import scenario

@scenario("Smoke: scenariusz dostawy do domu przechodzi do etapu checkout")
def test_order_delivery(...):
    ...
```

Equivalent marker form is also supported:

```python
@pytest.mark.scenario("Opis scenariusza")
```

When present, description is attached to:
- Loguru timing log (`test_case_timing`),
- reporting API `test_result` payload as `scenario`.
