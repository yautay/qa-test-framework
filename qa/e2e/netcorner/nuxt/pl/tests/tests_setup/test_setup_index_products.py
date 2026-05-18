from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.setup]


@pytest.mark.scenario("SetUpNUXT: TestSetUpIndexProducts")
def test_setup_index_products(admin_panel):
    erp_codes = NetcornerSetupService(admin_panel).reindex_products(RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS)
    assert erp_codes, "Nie zebrano żadnych kodów ERP do indeksowania produktów."
