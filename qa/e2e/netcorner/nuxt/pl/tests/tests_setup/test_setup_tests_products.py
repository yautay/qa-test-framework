from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.setup]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsProducts")
def test_setup_tests_products(admin_panel):
    NetcornerSetupService(admin_panel).recompute_product_purchase_eligibility(RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS)
