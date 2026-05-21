from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import SEZAM_PRODUCT_CASES
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.e2e_setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsPromotionsSezam")
@pytest.mark.parametrize("case", SEZAM_PRODUCT_CASES, ids=lambda case: case.case_id)
def test_setup_tests_promotions_sezam(admin_panel, case, setup_action_logger):
    NetcornerSetupService(admin_panel, setup_logger=setup_action_logger).save_existing_sezam_promotions(case.product_ids)
