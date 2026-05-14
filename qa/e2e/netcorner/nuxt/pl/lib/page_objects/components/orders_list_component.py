from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text


@dataclass(frozen=True, slots=True)
class OrderRowData:
    order_number: str
    status: str
    value: str


class OrderRowComponent(BaseComponent):
    """Represents a single order row in the customer account orders list.

    Root: ``[data-name='ordersGroupProduct']`` — one element per order.
    """

    ROOT_SELECTOR = "[data-name='ordersGroupProduct']"

    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Order Row Component")
        self.__order_status = self.find("[data-name='orderStatus']")
        self.__order_value = self.find("[data-name='orderValue']")
        self.__btn_details = self.root.get_by_role("button", name="Szczegóły zamówienia")
        self.__btn_cancel = self.root.get_by_role("button", name="Anuluj zamówienie")

    def get_order_number(self) -> str:
        """Extract order number from text like 'Zamówienie nr: 12345/2026'."""
        full_text = self.root.inner_text()
        match = re.search(r"\b(\d{4,}/\d{4})\b", full_text)
        return match.group(1) if match else ""

    def get_status(self) -> str:
        return get_visible_text(self.__order_status)

    def get_value(self) -> str:
        return get_visible_text(self.__order_value)

    def get_data(self) -> OrderRowData:
        return OrderRowData(
            order_number=self.get_order_number(),
            status=self.get_status(),
            value=self.get_value(),
        )

    def has_cancel_button(self) -> bool:
        return self.__btn_cancel.count() > 0 and self.__btn_cancel.is_visible()

    @step("Klikam 'Szczegóły zamówienia'")
    def click_details(self) -> None:
        self.pointer_click(self.__btn_details)

    @step("Klikam 'Anuluj zamówienie'")
    def click_cancel(self) -> None:
        self.pointer_click(self.__btn_cancel)


class OrdersListComponent(BaseComponent):
    """Orders list on the customer account page.

    Root: ``#pageContent`` scoped to the orders area.
    The list renders ``[data-name='ordersGroupProduct']`` items after hydration.
    """

    ROOT_SELECTOR = "#pageContent"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Orders List Component")

    @step("Czekam na załadowanie listy zamówień")
    def wait_orders_loaded(self, timeout: int = 15_000) -> Self:
        self.root.locator("[data-name='ordersGroupProduct']").first.wait_for(
            state="visible", timeout=timeout
        )
        return self

    def _rows(self) -> Locator:
        return self.root.locator("[data-name='ordersGroupProduct']")

    def count(self) -> int:
        return self._rows().count()

    def row(self, index: int = 0) -> OrderRowComponent:
        return OrderRowComponent(self._rows().nth(index))

    @step("Szukam zamówienia nr {order_number}")
    def find_order_by_number(self, order_number: str) -> OrderRowComponent | None:
        """Return the OrderRowComponent for the given order number, or None."""
        rows = self._rows()
        for i in range(rows.count()):
            row = OrderRowComponent(rows.nth(i))
            if row.get_order_number() == order_number:
                return row
        return None

    @step("Weryfikuję toast po próbie anulowania zamówienia")
    def expect_cancel_failure_toast_visible(self, timeout: int = 6_000) -> Self:
        """Assert the 'nie powiodło się' error toast is visible after a failed cancel."""
        toast = self.root.page.locator(
            "li[data-name*='toast'], [data-name='toast']"
        ).filter(has_text=re.compile(r"nie powiodło|anulowanie.*nie|nie można", re.IGNORECASE))
        expect(toast.first).to_be_visible(timeout=timeout)
        return self

    @step("Weryfikuję status zamówienia {order_number} to '{expected_status}'")
    def expect_order_status(self, order_number: str, expected_status: str, timeout: int = 8_000) -> Self:
        row = self.find_order_by_number(order_number)
        assert row is not None, f"Zamówienie {order_number} nie zostało znalezione na liście."
        status_locator = row.root.locator("[data-name='orderStatus']")
        expect(status_locator).to_have_text(re.compile(expected_status, re.IGNORECASE), timeout=timeout)
        return self
