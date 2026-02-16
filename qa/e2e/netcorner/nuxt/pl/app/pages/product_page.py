from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import ProductPageSelectors


class ProductPage(BasePage):
    def add_to_cart(self) -> bool:
        return self.click_first_visible(ProductPageSelectors.ADD_TO_CART_BUTTONS)
