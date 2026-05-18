from __future__ import annotations

import os

import pytest

from qa.e2e.netcorner.setup.setup_data import PROMOTION_SERVICE_PROMOTION_IDS
from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.setup]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsPromotionsService")
def test_setup_tests_promotions_service(page, runtime_env):
    promotion_ids = list(PROMOTION_SERVICE_PROMOTION_IDS.values())
    promotions_base_url = os.getenv("PROMOTIONS_BASE_URL", runtime_env.base_url)
    NetcornerSetupService(admin_panel=None, page=page).save_promotions_service(promotions_base_url, promotion_ids)
