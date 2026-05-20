from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.e2e_setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsProducts")
@pytest.mark.order(5)
def test_setup_tests_products(admin_panel, setup_action_logger):
    NetcornerSetupService(admin_panel, setup_logger=setup_action_logger).recompute_product_purchase_eligibility(
        RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS
    )
