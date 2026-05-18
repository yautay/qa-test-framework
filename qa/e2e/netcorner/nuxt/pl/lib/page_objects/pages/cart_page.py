from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content_section import CartContentSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer_section import CartFooterSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import CheckoutNavigationSection


class CartPage(BasePage):
    PATH = "/cart"
    PAGE_ID = "netcorner.pl.cart.main"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: CartContentSection | None = None
        self.__navigation: CheckoutNavigationSection | None = None
        self.__footer: CartFooterSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> CartPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.content.wait_visible()
        self.navigation.wait_visible()
        self.content.cart.wait_products_loaded()
        self.capture_dom_snapshot(event="page_loaded")
        return self

    @property
    def navigation(self) -> CheckoutNavigationSection:
        if self.__navigation is None:
            self.__navigation = CheckoutNavigationSection(self.page)
        return self.__navigation

    @property
    def content(self) -> CartContentSection:
        if self.__content is None:
            self.__content = CartContentSection(self.page)
        return self.__content

    @property
    def footer(self) -> CartFooterSection:
        if self.__footer is None:
            self.__footer = CartFooterSection(self.page)
        return self.__footer

    def proceed_to_checkout(self) -> CheckoutPage:
        self.footer.click_continue()
        Overlays(self.page).login.continue_without_login_if_visible()

        checkout_page = CheckoutPage(self.page, self.base_url)
        return checkout_page.wait_loaded()
