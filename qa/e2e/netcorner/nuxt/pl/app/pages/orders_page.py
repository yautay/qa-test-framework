from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import OrdersSelectors


class OrdersPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url.rstrip("/")

    def open_checkout(self) -> None:
        self.page.goto(f"{self.base_url}/checkout")

    def open_cart(self) -> None:
        self.page.goto(f"{self.base_url}/cart")

    def has_orders(self) -> bool:
        return self.locator(OrdersSelectors.ORDER_TILE).count() > 0

    def is_page_reachable(self) -> bool:
        return self.page.url.startswith(self.base_url)
