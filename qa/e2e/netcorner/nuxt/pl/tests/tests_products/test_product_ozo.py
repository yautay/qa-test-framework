from __future__ import annotations

import logging
from datetime import datetime

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_core,
    pytest.mark.xdist_group("orders_ozo_serial"),
]

# Produkt testowy OZO (Okazje z Odliczaniem) — stały produkt testowy na środowisku galak.test.
_OZO_TEST_PRODUCT_PATH = "/product/500000513/tusz-do-drukarki--test-product-produkt-ozo.html"
_OZO_PRODUCT_ID = 500000513
logger = logging.getLogger(__name__)


@pytest.fixture
def ozo_reset(admin_panel: AdminWrappers):
    admin_panel.reset_ozo_for_product(_OZO_PRODUCT_ID)
    yield
    try:
        admin_panel.reset_ozo_for_product(_OZO_PRODUCT_ID)
    except PlaywrightTimeoutError:
        logger.warning("Teardown reset OZO timeout for product_id=%s", _OZO_PRODUCT_ID)


@allure.feature("Produkty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Widget OZO na stronie głównej wyświetla kluczowe dane produktu")
def test_product_ozo(page, runtime_env, ozo_reset):
    home = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
    if not home.content.hero.is_ozo_widget_present():
        pytest.skip("Widget OZO nie jest widoczny na stronie głównej na tym środowisku.")
    home.content.hero.expect_ozo_widget_visible().expect_ozo_widget_has_core_data()


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Karta produktu OZO wyświetla komponent limitowanej sprzedaży")
def test_product_ozo_limited_sale_component(page, runtime_env, ozo_reset):
    product = ProductPage(page, runtime_env.base_url).open(_OZO_TEST_PRODUCT_PATH).wait_loaded()
    product.content.price.expect_limited_sale_visible()


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Produkt OZO ma spójne liczniki między homepage i kartą produktu")
def test_product_ozo_parameters_consistency(page, runtime_env, ozo_reset, admin_panel: AdminWrappers):
    settings = admin_panel.get_ozo_limited_sale_settings(_OZO_PRODUCT_ID)
    home = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
    if not home.content.hero.is_ozo_widget_present():
        pytest.skip("Widget OZO nie jest widoczny na stronie głównej na tym środowisku.")

    home.content.hero.expect_ozo_widget_has_core_data()
    home.content.hero.expect_ozo_previous_price_visible()
    box_data = home.content.hero.get_ozo_details()

    date_to = datetime.strptime(str(settings["date_to"]), "%Y-%m-%d %H:%M")
    days_left_expected = (date_to - datetime.now()).days
    assert abs(box_data.days_left - days_left_expected) <= 1, (
        "Liczba dni do końca promocji OZO na homepage jest niezgodna z ustawieniami admin. "
        f"Homepage={box_data.days_left}, admin={days_left_expected}."
    )

    product = ProductPage(page, runtime_env.base_url).open(_OZO_TEST_PRODUCT_PATH).wait_loaded()
    limited_sale = product.content.price.get_limited_sale_status()
    assert limited_sale is not None, "Brak komponentu limitowanej sprzedaży na karcie produktu OZO."
    assert box_data.sold_amount == limited_sale["limited_sale_sold"], (
        "Licznik sprzedanych sztuk OZO jest niespójny między homepage i kartą produktu."
    )
    assert box_data.remaining_amount == limited_sale["limited_sale_left"], (
        "Licznik pozostałych sztuk OZO jest niespójny między homepage i kartą produktu."
    )


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Produkt OZO pokazuje ograniczenie sprzedaży w koszyku")
def test_product_ozo_limited_sale_visibility_in_cart(page, runtime_env, ozo_reset):
    product = ProductPage(page, runtime_env.base_url).open(_OZO_TEST_PRODUCT_PATH).wait_loaded()
    limited_sale = product.content.price.get_limited_sale_status()
    if limited_sale is None:
        pytest.skip("Brak komponentu limitowanej sprzedaży na karcie produktu OZO.")

    product.add_to_cart()
    product.overlays.promotions.click_buy_only_product()
    product.overlays.go_to_cart.click_go_to_cart()

    cart = CartPage(page, runtime_env.base_url).wait_loaded()
    assert cart.content.cart.count() > 0, "Koszyk jest pusty po dodaniu produktu OZO."

    first_item = cart.content.cart.item(0)
    assert first_item.is_limited_sale_visible(), "Brak banera sprzedaży limitowanej dla produktu OZO w koszyku."
    quantity_before = first_item.get_quantity()
    first_item.click_increase_quantity()
    quantity_after = first_item.get_quantity()
    assert quantity_after == quantity_before, (
        "Ilość produktu OZO w koszyku zmieniła się mimo ograniczenia sprzedaży limitowanej."
    )
