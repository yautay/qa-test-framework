from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import CartSelectors


class CartPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url.rstrip("/")

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/cart")

    def is_ready(self) -> bool:
        return "/cart" in self.page.url and self.page.locator("body").first.is_visible()

    def has_interactive_cart_surface(self) -> bool:
        for selector in CartSelectors.INTERACTIVE_CANDIDATES:
            locator = self.page.locator(selector)
            count = locator.count()
            if count == 0:
                continue
            for idx in range(min(count, 15)):
                if locator.nth(idx).is_visible():
                    return True
        for keyword in CartSelectors.TEXT_CANDIDATES:
            if self.page.get_by_text(keyword, exact=False).first.is_visible():
                return True
        return False

    def move_further_to_checkout(self) -> bool:
        return self.click_first_visible(CartSelectors.PROCEED_TO_CHECKOUT_BUTTONS)
