from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import SEZAM_PRODUCT_CASES
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsPromotionsSezam")
@pytest.mark.parametrize("case", SEZAM_PRODUCT_CASES, ids=lambda case: case.case_id)
def test_setup_tests_promotions_sezam(admin_panel, case):
    NetcornerSetupService(admin_panel).save_existing_sezam_promotions(case.product_ids)
