from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState


class AdminOrdersPage(AdminBasePage):
    """Admin orders list page.

    URL: <admin_base_url>/admin.php/orders/list/pl
    Confirmed live against komputronik-galak env (2026-05-14).

    Key locators (derived from live HTML):
        <h1>Lista zamówień</h1>
        <table class="sf_admin_list"> — the orders table
        <a title="{order_number}" href="/admin.php/orders/edit/pl/order_id/{id}">
    """

    PAGE_ID = "netcorner.admin.orders.list"
    PATH = "/admin.php/orders/list/pl"

    _LOC_PAGE_HEADER = "h1:has-text('Lista zamówień')"
    _LOC_ADMIN_CONTAINER = "#sf_admin_container"
    # Order links have title in format "NNNNNN/YYYY" — use regex-like selector to avoid
    # matching menu/icon links which either have no title or non-numeric titles.
    # CSS: a[title][href*='order_id'] — but edit icon links have title="" so we filter
    # further by requiring title to match order number pattern via :not([title=""])
    _LOC_ORDER_LINK_BY_NUMBER = "a[title='{order_number}'][href*='order_id']"
    _LOC_ANY_ORDER_LINK = "a[href*='order_id']:not([title=''])"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminOrdersPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.page.locator(self._LOC_PAGE_HEADER).wait_for(state="visible", timeout=10_000)
        return self

    def open_order(self, order_number: str) -> None:
        """Click the order link for the given order number.

        Args:
            order_number: Full order number string, e.g. '181255/2026'.
        """
        locator = self.page.locator(
            self._LOC_ORDER_LINK_BY_NUMBER.format(order_number=order_number)
        )
        locator.wait_for(state="visible", timeout=10_000)
        locator.click()
        self.page.wait_for_load_state("domcontentloaded")

    def open_first_order(self) -> None:
        """Click the first order in the list (for smoke checks)."""
        first = self.page.locator(self._LOC_ANY_ORDER_LINK).first
        first.wait_for(state="visible", timeout=10_000)
        first.click()
        self.page.wait_for_load_state("domcontentloaded")

    def navigate_to(self) -> AdminOrdersPage:
        """Navigate directly to the orders list URL."""
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()


__all__ = ["AdminOrdersPage"]
