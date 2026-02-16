from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.app.data.orders_smoke_data import ORDER_SMOKE_CASES
from qa.e2e.netcorner.nuxt.pl.app.services.order_flow_service import OrderFlowService

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.parametrize("case", ORDER_SMOKE_CASES, ids=[case.case_id for case in ORDER_SMOKE_CASES])
def test_order_full_process(page, context, runtime_env, case):
    if not runtime_env.base_url:
        pytest.skip("BASE_URL not set")

    assert context.cookies() == []
    flow = OrderFlowService(page, runtime_env.base_url)
    result = flow.run_full_checkout(case)
    assert result["order_number"], f"Order number missing for case {case.case_id}"
