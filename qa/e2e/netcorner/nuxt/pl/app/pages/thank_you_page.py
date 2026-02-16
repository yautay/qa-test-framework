from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import ThankYouSelectors


class ThankYouPage(BasePage):
    def wait_for_order_number(self) -> str:
        self.expect_visible(ThankYouSelectors.ORDER_NUMBER)
        return self.locator(ThankYouSelectors.ORDER_NUMBER).first.inner_text().strip()

    def has_summary_price(self) -> bool:
        return self.locator(ThankYouSelectors.ORDER_SUMMARY).count() > 0
