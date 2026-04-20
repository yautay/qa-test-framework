from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Locator, Page, expect

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


def _normalize_price(text: str) -> str:
    match = re.search(r"([\d\s]+(?:[\.,]\d{2})?)", text)
    if match:
        return match.group(1).replace(" ", "")
    return text


class ProductRecapComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='productRecapInfo']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Product Recap Component")
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
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Product Price Component")

    def __resolved_root(self) -> Locator:
        resolved_root = self.root.page.locator(f"{self.ROOT_SELECTOR}:visible").first
        expect(resolved_root).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        return resolved_root

    @step("Dodaję produkt do koszyka")
    def add_to_cart(self) -> ProductPriceData:
        data = self.get_data()
        add_to_cart_button = self.__resolved_root().locator("[data-name='addToCartButton']:visible").first
        self.safe_click(add_to_cart_button)
        return data

    def get_data(self) -> ProductPriceData:
        root = self.__resolved_root()
        final_price = root.locator("[data-price-type='final']").first
        availability_status_locator = root.locator("[data-name='statusAvailable'] .font-semibold").first
        free_shipping = root.locator("[data-name='freeShipping']").first

        status_text = _get_visible_text(availability_status_locator)
        availability_status: AvailabilityStatus | None = None
        if status_text:
            try:
                availability_status = AvailabilityStatuses.from_status_text(status_text)
            except ValueError:
                availability_status = None

        return ProductPriceData(
            final_price=_normalize_price(_get_visible_text(final_price)),
            availability_status=availability_status,
            free_shipping=free_shipping.count() > 0 and free_shipping.is_visible(),
        )
