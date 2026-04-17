from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import (
    AvailabilityStatus,
    AvailabilityStatuses,
)


def _get_visible_text(locator: Locator) -> str:
    element = locator.first
    if element.count() == 0 or not element.is_visible():
        return ""
    return (element.text_content() or "").strip()


class ProductComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='productRecapInfo']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Listing Filters Component")
        self.__product_name = self.find("[data-name='productName']")
        self.__system_code = self.find("p").filter(has_text="Kod systemowy:")
        self.__reviews_link = self.find("a[href='#Opinie']")

    def get_product_name(self) -> str:
        return _get_visible_text(self.__product_name)

    def get_system_code(self) -> str:
        return _get_visible_text(self.__system_code).replace("Kod systemowy:", "").strip()

    def get_reviews(self) -> str:
        return _get_visible_text(self.__reviews_link)


class ProductPriceComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='addToCartWrapper']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Listing Filters Component")

        self.__final_price = self.find("[data-price-type='final']")
        self.__add_to_cart_button = self.find("[data-name='addToCartButton']")
        self.__availability_status = self.find("[data-name='statusAvailable']")
        self.__free_shipping = self.find("[data-name='freeShipping']")

    @step("Dodaję produkt do koszyka")
    def add_to_cart(self) -> None:
        self.safe_click(self.__add_to_cart_button)

    def get_final_price(self) -> str:
        return _get_visible_text(self.__final_price).replace(" ", "")

    def get_availability_status(self) -> AvailabilityStatus | None:
        status_text = _get_visible_text(self.__availability_status)
        if not status_text:
            return None
        try:
            return AvailabilityStatuses.from_status_text(status_text)
        except ValueError:
            return None

    def get_free_shipping(self) -> bool:
        free_shipping = self.__free_shipping.first
        return free_shipping.count() > 0 and free_shipping.is_visible()
