from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text, normalize_price, strip_prefix
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


class ProductRecapComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='productPrimaryInfo']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Product Recap Component")
        self.__product_name = self.find("[data-name='productName']")
        self.__system_code = self.find("p").filter(has_text="Kod systemowy:")
        self.__reviews_link = self.find("a[href='#Opinie']")

    def get_data(self) -> ProductRecapData:
        product_name_element = self.__product_name.first
        product_name_element.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        product_name = (product_name_element.text_content() or "").strip()

        return ProductRecapData(
            product_name=product_name,
            system_code=strip_prefix(get_visible_text(self.__system_code), "Kod systemowy:"),
            reviews=get_visible_text(self.__reviews_link),
        )


class ProductActionsComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Product Actions Component")
        self.__compare_button = self.find("button[title='Porównaj'][data-name='productAction']")
        self.__wishlist_button = self.find("button[title='Lista życzeń'][data-name='productAction']")
        self.__print_button = self.find("button[title='Drukuj'][data-name='productAction']")

    @step("Klikam Porównaj")
    def click_compare(self) -> None:
        self.pointer_click(self.__compare_button)

    @step("Klikam Lista życzeń")
    def click_wishlist(self) -> None:
        self.pointer_click(self.__wishlist_button)

    @step("Klikam Drukuj")
    def click_print(self) -> None:
        self.pointer_click(self.__print_button)


class ProductPriceComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='addToCartWrapper']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Product Price Component")

    def __resolved_root(self) -> Locator:
        """Resolve to the visible addToCartWrapper (handles desktop/mobile responsive variants).

        The product page may render two wrappers (mobile + desktop).
        Only one is visible at any viewport; the other has ``display: none``.
        Both appear asynchronously after navigation, so we must wait.
        """
        candidates = self._root_candidates
        # Single browser round-trip: wait until ANY wrapper is visible
        self.root.page.wait_for_function(
            """selector => {
                const els = document.querySelectorAll(selector);
                return Array.from(els).some(el => {
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return r.width > 0 && r.height > 0
                        && s.visibility !== 'hidden' && s.display !== 'none';
                });
            }""",
            arg=self.ROOT_SELECTOR,
            timeout=self.DEFAULT_TIMEOUT,
        )
        # Pick the visible one
        for i in range(candidates.count()):
            candidate = candidates.nth(i)
            if candidate.is_visible():
                self.root = candidate
                return self.root
        self.root = candidates.first
        return self.root

    @step("Dodaję produkt do koszyka")
    def add_to_cart(self) -> ProductPriceData:
        data = self.get_data()
        add_to_cart_button = self.root.locator("[data-name='addToCartButton']").first
        self.pointer_click(add_to_cart_button)
        return data

    def get_data(self) -> ProductPriceData:
        self.__resolved_root()
        final_price = self.find("[data-price-type='final']").first
        availability_status_locator = self.find("[data-name='statusAvailable'] .font-semibold").first
        free_shipping = self.find("[data-name='freeShipping']").first

        status_text = get_visible_text(availability_status_locator)
        availability_status: AvailabilityStatus | None = None
        if status_text:
            try:
                availability_status = AvailabilityStatuses.from_status_text(status_text)
            except ValueError:
                availability_status = None

        return ProductPriceData(
            final_price=normalize_price(get_visible_text(final_price)),
            availability_status=availability_status,
            free_shipping=free_shipping.count() > 0 and free_shipping.is_visible(),
        )
