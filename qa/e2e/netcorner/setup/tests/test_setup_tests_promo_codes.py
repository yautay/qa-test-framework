from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_flows import NetcornerSetupService

pytestmark = [pytest.mark.setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsPromoCodes")
def test_setup_tests_promo_codes(admin_panel):
    NetcornerSetupService(admin_panel).ensure_promo_codes()
