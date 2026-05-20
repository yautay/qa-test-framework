from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.e2e_setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpIndexProducts")
@pytest.mark.order(6)
def test_setup_index_products(admin_panel):
    erp_codes = NetcornerSetupService(admin_panel).reindex_products(RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS)
    assert erp_codes, "Nie zebrano żadnych kodów ERP do indeksowania produktów."
