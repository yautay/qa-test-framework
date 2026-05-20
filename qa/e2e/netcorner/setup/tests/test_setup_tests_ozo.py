from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.setup.setup_data import OZO_TEST_PRODUCT_ID

pytestmark = [pytest.mark.e2e_setup, pytest.mark.target("netcorner-nuxt-pl")]


@pytest.mark.scenario("SetUpNUXT: TestSetUpTestsOzo")
@pytest.mark.order(4)
def test_setup_tests_ozo(admin_panel, page, runtime_env):
    admin_panel.reset_ozo_for_product(OZO_TEST_PRODUCT_ID)
    admin_panel.save_existing_product_promotion(OZO_TEST_PRODUCT_ID)

    frontend_base_url = runtime_env.base_url or f"https://komputronik-{runtime_env.server_name}.netcorner.pl"
    home = HomePage(page, frontend_base_url).open(HomePage.PATH).wait_loaded()
    assert home.content.hero.is_ozo_widget_present(timeout_ms=10_000), (
        "Widget OZO nie jest widoczny po setupie. "
        "Sprawdź przypięcie produktu 500000513 do boxa OZO na homepage (box_id=2) oraz cache środowiska."
    )
    home.content.hero.expect_ozo_widget_has_core_data(timeout_ms=10_000)
