from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.e2e_setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsPromoCodes")
def test_setup_tests_promo_codes(admin_panel, setup_action_logger):
    NetcornerSetupService(admin_panel, setup_logger=setup_action_logger).ensure_promo_codes()
