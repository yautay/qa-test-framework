from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text


@dataclass(frozen=True, slots=True)
class CartProductData:
    product_id: str
    product_name: str
    unit_price_gross: str
    total_price_gross: str
    availability_status: str
    quantity: int


@dataclass(frozen=True, slots=True)
class CartSummaryData:
    products_value_gross: str
    products_value_net: str
    installment_info: str


class CartProductComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='cartProduct']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Cart Product Component")

        self.__increase_quantity_button = self.find("button[aria-label='Zwiększ ilość o 1']")
        self.__decrease_quantity_button = self.find("button[aria-label='Zmniejsz ilość o 1']")
        self.__quantity_input = self.find("input[type='number'][aria-label^='liczba:']")
        self.__total_price_gross = self.find("[data-name='cartProductTotal'] [data-price-type='gross']")
        self.__remove_product = self.find("[data-name='deleteProduct']")
        self.__unit_price_gross = self.find("[data-name='cartProductPrice'] [data-price-type='gross']")
        self.__product_name_link = self.find("[data-name='cartProductMain'] .ml-4 a")
        self.__availability_status_text = self.find("[data-name='statusAvailable'] .font-semibold")
        self.__limited_sale_banner = self.find("p:has-text('Sprzedaż limitowana')")
        self.__hide_addons_button = self.find("button:has-text('Ukryj dodatki')")
        self.__show_addons_button = self.find("button:has-text('Sprawdź dodatki')")

    @step("Klikam plus (zwiększam ilość)")
    def click_increase_quantity(self) -> Self:
        self.pointer_click(self.__increase_quantity_button)
        return self

    def can_increase_quantity(self) -> bool:
        button = self.__increase_quantity_button.first
        return button.count() > 0 and button.is_visible() and button.is_enabled()

    @step("Klikam minus (zmniejszam ilość)")
    def click_decrease_quantity(self) -> Self:
        self.pointer_click(self.__decrease_quantity_button)
        return self

    @step("Ustawiam ilość produktu na: {value}")
    def enter_quantity(self, value: int | str) -> Self:
        self.safe_fill(self.__quantity_input, str(value))
        return self

    @step("Klikam usuń produkt")
    def click_remove_product(self) -> None:
        self.pointer_click(self.__remove_product)

    @step("Klikam 'Ukryj dodatki'")
    def click_hide_addons(self) -> Self:
        self.pointer_click(self.__hide_addons_button)
        return self

    @step("Klikam 'Sprawdź dodatki'")
    def click_show_addons(self) -> Self:
        self.pointer_click(self.__show_addons_button)
        return self

    @step("Przełączam dodatki produktu")
    def click_toggle_addons(self) -> Self:
        hide_button = self.__hide_addons_button.first
        if hide_button.count() > 0 and hide_button.is_visible():
            self.pointer_click(hide_button)
            return self

        show_button = self.__show_addons_button.first
        if show_button.count() > 0 and show_button.is_visible():
            self.pointer_click(show_button)
        return self

    def get_product_id(self) -> str:
        return (self.root.get_attribute("data-product-id") or "").strip()

    def get_total_price_gross(self) -> str:
        return get_visible_text(self.__total_price_gross)

    def get_unit_price_gross(self) -> str:
        return get_visible_text(self.__unit_price_gross)

    def get_product_name(self) -> str:
        return get_visible_text(self.__product_name_link)

    def get_availability_status(self) -> str:
        return get_visible_text(self.__availability_status_text)

    def get_quantity(self) -> int:
        raw = (self.__quantity_input.input_value() or "").strip()
        try:
            return int(raw)
        except ValueError:
            return 0

    def is_limited_sale_visible(self, timeout: int = 5_000) -> bool:
        banner = self.__limited_sale_banner.first
        return banner.count() > 0 and banner.is_visible(timeout=timeout)

    def get_limited_sale_text(self) -> str:
        return get_visible_text(self.__limited_sale_banner)

    def get_data(self) -> CartProductData:
        return CartProductData(
            product_id=self.get_product_id(),
            product_name=self.get_product_name(),
            unit_price_gross=self.get_unit_price_gross(),
            total_price_gross=self.get_total_price_gross(),
            availability_status=self.get_availability_status(),
            quantity=self.get_quantity(),
        )


class CartComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='cartProducts']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Cart Products Component")
        self.__product_groups = self.find("[data-name='cartProductGroup']")

    @step("Czekam na załadowanie produktów w koszyku")
    def wait_products_loaded(self, timeout: int = 15_000) -> Self:
        self.root.wait_for(state="visible", timeout=timeout)
        self.__product_groups.first.wait_for(state="visible", timeout=timeout)
        return self

    def count(self) -> int:
        return self.__product_groups.count()

    def item(self, index: int) -> CartProductComponent:
        return CartProductComponent(self.__product_groups.nth(index))

    def items(self) -> list[CartProductComponent]:
        return [self.item(index) for index in range(self.count())]

    def get_product_ids(self) -> list[str]:
        return [product.get_product_id() for product in self.items()]

    @step("Wyszukuję produkt w koszyku po ID: {product_id}")
    def get_product(self, product_id: str) -> CartProductComponent | None:
        for product in self.items():
            if product.get_product_id() == product_id:
                return product
        return None

    def get_data(self) -> dict[str, CartProductData]:
        products_data: dict[str, CartProductData] = {}
        for product in self.items():
            data = product.get_data()
            if not data.product_id:
                raise ValueError("Cart product is missing data-product-id attribute")
            if data.product_id in products_data:
                raise ValueError(f"Duplicate cart product id detected: {data.product_id}")
            products_data[data.product_id] = data
        return products_data


class CartSummaryComponent(BaseComponent):
    ROOT_SELECTOR = "[data-role='cartSummary']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Cart Summary Component")

        self.__coupon_code_input = self.find("#couponCode")
        self.__add_coupon_code_button = self.find("button:has-text('Dodaj kod')")
        self.__calculate_installment_button = self.find("button:has-text('Oblicz ratę')")
        self.__products_value_gross = self.root.locator(
            "xpath=.//div[p[contains(normalize-space(.), 'Wartość produktów:')]]"
            "//div[contains(@class, 'text-right')]//p[1]"
        )
        self.__products_value_net = self.root.locator(
            "xpath=.//div[p[contains(normalize-space(.), 'Wartość produktów:')]]//p[@data-price-type='net']"
        )
        self.__installment_info_text = self.find("p:has-text('Rata już od')")

    @step("Wpisuję kod promocyjny: {value}")
    def enter_coupon_code(self, value: str) -> Self:
        self.safe_fill(self.__coupon_code_input, value)
        return self

    @step("Klikam 'Dodaj kod'")
    def click_add_coupon_code(self) -> Self:
        self.pointer_click(self.__add_coupon_code_button)
        return self

    @step("Klikam 'Oblicz ratę'")
    def click_calculate_installment(self) -> Self:
        self.pointer_click(self.__calculate_installment_button)
        return self

    def get_products_value(self) -> str:
        return get_visible_text(self.__products_value_gross)

    def get_products_value_net(self) -> str:
        return get_visible_text(self.__products_value_net)

    def get_installment_info(self) -> str:
        return get_visible_text(self.__installment_info_text)

    def get_data(self) -> CartSummaryData:
        return CartSummaryData(
            products_value_gross=self.get_products_value(),
            products_value_net=self.get_products_value_net(),
            installment_info=self.get_installment_info(),
        )
