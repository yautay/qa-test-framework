from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Widget OZO na stronie głównej wyświetla kluczowe dane produktu")
def test_product_ozo(page, runtime_env):
    home = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
    home.content.hero.expect_ozo_widget_visible().expect_ozo_widget_has_core_data()
