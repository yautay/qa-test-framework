from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import LayerSelectors


class LayerPage(BasePage):
    def close_recommendation_if_visible(self) -> None:
        self.click_first_visible(LayerSelectors.CLOSE_RECOMMENDATION_BUTTONS, timeout=1000)

    def go_to_cart_if_visible(self) -> bool:
        return self.click_first_visible(LayerSelectors.GO_TO_CART_BUTTONS, timeout=2500)
