from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


@dataclass(frozen=True, slots=True)
class TypSummaryData:
    order_number: str | None
    planned_delivery: str | None
    delivery_address: str | None
    delivery_cost: str | None
    sms_status_cost: str | None
    payment_cost: str | None
    total_to_pay: str | None


class TypSummaryComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="TypSummaryComponent")

        self.__order_number = self.find("p.text-lg.font-medium")
        self.__planned_delivery = self.find("p:has-text('Planowana dostawa twojego zamówienia:') + div span")
        self.__delivery_address = self.find("p:has-text('Adres dostawy:') + div span")
        self.__delivery_cost = self.find("span:text-is('Dostawa') + span.font-semibold")
        self.__sms_status_cost = self.find("span:text-is('SMS Status zamówienia') + span.font-semibold")
        self.__payment_cost = self.find("p:text-is('Płatność') + div span.block.text-right")
        self.__total_to_pay = self.find("p:text-is('Do zapłaty') + span span.block.text-right")

    @staticmethod
    def __safe_text(locator: Locator) -> str | None:
        target = locator.first
        if target.count() == 0:
            return None

        text = target.text_content()
        if text is None:
            return None

        return text.strip()

    def __get_order_number(self) -> str | None:
        return (self.__order_number.text_content() or "").strip()

    def __get_planned_delivery(self) -> str | None:
        return self.__safe_text(self.__planned_delivery)

    def __get_delivery_address(self) -> str | None:
        return self.__safe_text(self.__delivery_address)

    def __get_delivery_cost(self) -> str | None:
        return self.__safe_text(self.__delivery_cost)

    def __get_sms_status_cost(self) -> str | None:
        return self.__safe_text(self.__sms_status_cost)

    def __get_payment_cost(self) -> str | None:
        return self.__safe_text(self.__payment_cost)

    def __get_total_to_pay(self) -> str | None:
        return self.__safe_text(self.__total_to_pay)

    def get_summary_data(self) -> TypSummaryData:
        return TypSummaryData(
            order_number=self.__get_order_number(),
            planned_delivery=self.__get_planned_delivery(),
            delivery_address=self.__get_delivery_address(),
            delivery_cost=self.__get_delivery_cost(),
            sms_status_cost=self.__get_sms_status_cost(),
            payment_cost=self.__get_payment_cost(),
            total_to_pay=self.__get_total_to_pay(),
        )
