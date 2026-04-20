from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content_section import ConfiguratorContentSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer_section import FooterSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.header_section import HeaderSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import NavigationSection


class CartPage(BasePage):
    PATH = "/cart"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: CartContentSection | None = None
        self.__navigation: NavigationSection | None = None
        self.__header: HeaderSection | None = None
        self.__footer: FooterSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> CartPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
        self.content.wait_visible()
        self.navigation.wait_visible()
        self.footer.wait_visible()
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
    def content(self) -> CartContentSection:
        if self.__content is None:
            self.__content = CartContentSection(self.page)
        return self.__content

    @property
    def footer(self) -> FooterSection:
        if self.__footer is None:
            self.__footer = FooterSection(self.page)
        return self.__footer
