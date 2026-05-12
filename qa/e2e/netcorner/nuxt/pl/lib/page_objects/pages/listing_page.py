from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import ListingProductData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages import my_account_page, product_page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content_section import ListingContentSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer_section import FooterSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.header_section import HeaderSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import NavigationSection
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import AvailabilityStatus


class ListingPage(BasePage):
    PAGE_ID = "netcorner.pl.listing.category"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: ListingContentSection | None = None
        self.__navigation: NavigationSection | None = None
        self.__header: HeaderSection | None = None
        self.__footer: FooterSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> ListingPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
        self.content.wait_visible()
        self.navigation.wait_visible()
        self.footer.wait_visible()
        self.capture_dom_snapshot(event="page_loaded")
        return self

    @property
    def header(self) -> HeaderSection:
        if self.__header is None:
            self.__header = HeaderSection(self.page)
        return self.__header

    @property
    def navigation(self) -> NavigationSection:
        if self.__navigation is None:
            self.__navigation = NavigationSection(self.page)
        return self.__navigation

    @property
    def content(self) -> ListingContentSection:
        if self.__content is None:
            self.__content = ListingContentSection(self.page)
        return self.__content

    @property
    def footer(self) -> FooterSection:
        if self.__footer is None:
            self.__footer = FooterSection(self.page)
        return self.__footer

    def open_login_overlay(self):
        self.header.actions.open_login()
        return self.overlays.login.wait_visible()

    def open_account_page(self) -> my_account_page.MyAccountPage:
        self.header.actions.open_account()
        return my_account_page.MyAccountPage(self.page, self.base_url).wait_loaded()

    def open_first_product_by_shipping_status(
        self,
        shipping_status: AvailabilityStatus,
    ) -> tuple[ListingProductData, product_page.ProductPage] | None:
        while True:
            product_tile = self.content.content.find_first_product_by_shipping_status(shipping_status)
            if product_tile is not None:
                product_data = product_tile.get_data()
                product_tile.click_see_more()
                return product_data, product_page.ProductPage(self.page, self.base_url).wait_loaded()

            if not self.content.content.go_to_next_page():
                return None
