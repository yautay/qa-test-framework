from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import (
    AvailabilityStatus,
    AvailabilityStatuses,
)


@dataclass(frozen=True, slots=True)
class ProductRecapData:
    product_name: str
    system_code: str
    reviews: str


@dataclass(frozen=True, slots=True)
class ProductPriceData:
    final_price: str
    availability_status: AvailabilityStatus | None
    free_shipping: bool


@dataclass(frozen=True, slots=True)
class ProductComponentsData:
    recap: ProductRecapData
    price: ProductPriceData


def _get_visible_text(locator: Locator) -> str:
    element = locator.first
    if element.count() == 0 or not element.is_visible():
        return ""
    return (element.text_content() or "").strip()


def _strip_prefix(text: str, prefix: str) -> str:
    return text.removeprefix(prefix).strip()


class ProductRecapComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='productRecapInfo']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Product Recap Component")
        self.__product_name = self.find("[data-name='productName']")
        self.__system_code = self.find("p").filter(has_text="Kod systemowy:")
        self.__reviews_link = self.find("a[href='#Opinie']")

    def get_data(self) -> ProductRecapData:
        return ProductRecapData(
            product_name = _get_visible_text(self.__product_name),
            system_code = _strip_prefix(_get_visible_text(self.__system_code), "Kod systemowy:"),
            reviews= _get_visible_text(self.__reviews_link),
        )


class ProductPriceComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='addToCartWrapper']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Product Price Component")

        self.__final_price = self.find("[data-price-type='final']")
        self.__add_to_cart_button = self.find("[data-name='addToCartButton']")
        self.__availability_status = self.find("[data-name='statusAvailable']")
        self.__free_shipping = self.find("[data-name='freeShipping']")

    @step("Dodaję produkt do koszyka")
    def add_to_cart(self) -> ProductPriceData:
        data = self.get_data()
        self.safe_click(self.__add_to_cart_button)
        return data

    def get_data(self) -> ProductPriceData:
        status_text = _get_visible_text(self.__availability_status)
        availability_status: AvailabilityStatus | None = None
        if status_text:
            try:
                availability_status = AvailabilityStatuses.from_status_text(status_text)
            except ValueError:
                availability_status = None

        free_shipping = self.__free_shipping.first
        return ProductPriceData(
            final_price=_get_visible_text(self.__final_price).replace(" ", ""),
            availability_status=availability_status,
            free_shipping=free_shipping.count() > 0 and free_shipping.is_visible(),
        )
