from __future__ import annotations

import pytest

from qa.e2e.netcorner.setup.setup_data import OZO_TEST_PRODUCT_ID

pytestmark = [pytest.mark.e2e_setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsOzo")
@pytest.mark.order(4)
def test_setup_tests_ozo(admin_panel):
    admin_panel.reset_ozo_for_product(OZO_TEST_PRODUCT_ID)
