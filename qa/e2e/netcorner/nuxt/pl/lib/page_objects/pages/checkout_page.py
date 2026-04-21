from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.checkout_components import CheckoutSummaryData, TypSummaryData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content_section import (
    CheckoutContentSection,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import (
    CheckoutNavigationSection,
)


class CheckoutPage(BasePage):
    PATH = "/order/checkout"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: CheckoutContentSection | None = None
        self.__navigation: CheckoutNavigationSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> CheckoutPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.content.wait_visible()
        self.navigation.wait_visible()
        return self

    @property
    def navigation(self) -> CheckoutNavigationSection:
        if self.__navigation is None:
            self.__navigation = CheckoutNavigationSection(self.page)
        return self.__navigation

    @property
    def content(self) -> CheckoutContentSection:
        if self.__content is None:
            self.__content = CheckoutContentSection(self.page)
        return self.__content

    def submit_order(self) -> tuple[CheckoutSummaryData, TypSummaryData]:
        summary_data = self.content.summary.wait_visible().click_place_order()
        typ_summary_data = self.content.typ_summary.wait_visible().get_summary_data()
        return summary_data, typ_summary_data
