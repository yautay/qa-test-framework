from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage

pytestmark = [pytest.mark.e2e]

# Produkt testowy OZO (Okazje z Odliczaniem) — stały produkt testowy na środowisku galak.test.
_OZO_TEST_PRODUCT_PATH = "/product/500000513/tusz-do-drukarki--test-product-produkt-ozo.html"


@allure.feature("Produkty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Widget OZO na stronie głównej wyświetla kluczowe dane produktu")
def test_product_ozo(page, runtime_env):
    home = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
    home.content.hero.expect_ozo_widget_visible().expect_ozo_widget_has_core_data()


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Karta produktu OZO wyświetla komponent limitowanej sprzedaży")
def test_product_ozo_limited_sale_component(page, runtime_env):
    product = ProductPage(page, runtime_env.base_url).open(_OZO_TEST_PRODUCT_PATH).wait_loaded()
    product.content.price.expect_limited_sale_visible()
