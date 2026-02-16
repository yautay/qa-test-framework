from __future__ import annotations

from urllib.parse import urljoin

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import (
    ProductListSelectors,
    ProductPageSelectors,
)


class ProductListPage(BasePage):
    def __init__(self, page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url.rstrip("/")

    def open_category(self, category_path: str) -> None:
        self.page.goto(f"{self.base_url}/{category_path.lstrip('/')}")

    def apply_digital_filter_if_visible(self) -> None:
        try:
            self.page.get_by_text(ProductListSelectors.DIGITAL_LICENSE_FILTER_TEXT, exact=False).first.click(
                timeout=2000
            )
        except Exception:
            return

    def open_first_product(self) -> bool:
        for selector in ProductListSelectors.PRODUCT_LINKS:
            links = self.locator(selector)
            count = links.count()
            if count == 0:
                continue
            for idx in range(min(count, 8)):
                try:
                    links.nth(idx).click(timeout=3000)
                    return True
                except Exception:
                    continue
        return False

    def add_first_product_to_cart(self) -> bool:
        return self.click_first_visible(ProductListSelectors.ADD_TO_CART_BUTTONS)

    def search_product(self, phrase: str) -> bool:
        self.page.goto(self.base_url)
        filled = self.fill_first_visible(ProductListSelectors.SEARCH_INPUTS, phrase)
        if not filled:
            return False
        if self.click_first_visible(ProductListSelectors.SEARCH_SUBMIT_BUTTONS):
            return True
        self.page.keyboard.press("Enter")
        return True

    def add_buyable_product_to_cart(self, max_links: int = 12) -> bool:
        hrefs: list[str] = []
        for selector in ProductListSelectors.PRODUCT_LINKS:
            links = self.locator(selector)
            count = links.count()
            if count == 0:
                continue
            for idx in range(min(count, max_links)):
                href = links.nth(idx).get_attribute("href")
                if not href:
                    continue
                if href not in hrefs:
                    hrefs.append(href)
            if hrefs:
                break

        for href in hrefs:
            self.page.goto(urljoin(self.base_url + "/", href))
            if self.click_first_visible(ProductPageSelectors.ADD_TO_CART_BUTTONS, timeout=2000):
                return True
        return False
