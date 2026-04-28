from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text


@dataclass(frozen=True, slots=True)
class CheckoutSummaryData:
    delivery_price: str
    delivery_surcharge: Decimal
    total_to_pay: str


class CheckoutSummaryComponent(BaseComponent):
    SUMMARY_HEADING = "Podsumowanie koszyka"

    def __init__(self, scope: Page | Locator) -> None:
        page = scope if isinstance(scope, Page) else scope.page
        summary_panel = scope.locator("section,div,aside").filter(
            has=page.get_by_role("heading", name=self.SUMMARY_HEADING)
        )
        super().__init__(summary_panel, name="Checkout Summary Component")

        self.__delivery_price = self.find("css=div:has(> span:text-is('Dostawa')) >> span.font-semibold")
        self.__payment_fee = self.find("css=p:text-is('Płatność') + div >> span.block.text-right")
        self.__total_to_pay = self.find("css=p.font-semibold:text-is('Do zapłaty') + span >> span.block.text-right")
        self.__place_order_button = self.root.get_by_role("button", name="Zamawiam z obowiązkiem zapłaty").first

    @staticmethod
    def __read_text(locator: Locator) -> str:
        return get_visible_text(locator)

    @staticmethod
    def __parse_money(value: str) -> Decimal:
        match = re.search(r"([+-]?\d+(?:[\.,]\d{1,2})?)", value)
        if not match:
            return Decimal("0.00")
        try:
            return Decimal(match.group(1).replace(",", ".")).quantize(Decimal("0.01"))
        except InvalidOperation:
            return Decimal("0.00")

    @step("Klikam przycisk złożenia zamówienia")
    def click_place_order(self) -> CheckoutSummaryData:
        summary_data = CheckoutSummaryData(
            delivery_price=self.__get_delivery_price(),
            delivery_surcharge=self.__parse_money(self.__get_payment_fee()),
            total_to_pay=self.__get_total_to_pay(),
        )
        self.pointer_click(self.__place_order_button)
        return summary_data

    def __get_delivery_price(self) -> str:
        return self.__read_text(self.__delivery_price)

    def __get_payment_fee(self) -> str:
        return self.__read_text(self.__payment_fee)

    def __get_total_to_pay(self) -> str:
        return self.__read_text(self.__total_to_pay)
