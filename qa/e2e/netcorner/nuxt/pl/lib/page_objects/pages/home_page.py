from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages import configurator_page, my_account_page, register_page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content_section import HeroPageContentSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer_section import FooterSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.header_section import HeaderSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import NavigationSection


class HomePage(BasePage):
    PATH = "/"
    PAGE_ID = "netcorner.pl.home.main"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: HeroPageContentSection | None = None
        self.__header: HeaderSection | None = None
        self.__navigation: NavigationSection | None = None
        self.__footer: FooterSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> HomePage:
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
        self.navigation.wait_visible()
        self.content.wait_visible()
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
    def content(self) -> HeroPageContentSection:
        if self.__content is None:
            self.__content = HeroPageContentSection(self.page)
        return self.__content

    @property
    def footer(self) -> FooterSection:
        if self.__footer is None:
            self.__footer = FooterSection(self.page)
        return self.__footer

    def open_login_overlay(self):
        self.header.actions.open_login()
        return self.overlays.login.wait_visible()

    def open_register_page(self) -> register_page.RegisterPage:
        self.open_login_overlay().enter_register_form()
        return register_page.RegisterPage(self.page, self.base_url).wait_loaded()

    def open_account_page(self) -> my_account_page.MyAccountPage:
        self.header.actions.open_account()
        return my_account_page.MyAccountPage(self.page, self.base_url).wait_loaded()

    def open_configurator_from_banner(self) -> configurator_page.ConfiguratorPage:
        self.content.hero.go_to_pc_configurator_from_banner()
        return configurator_page.ConfiguratorPage(self.page, self.base_url).wait_loaded()

    def open_configurator_from_swiper(self) -> configurator_page.ConfiguratorPage:
        self.content.hero.go_to_pc_configurator_from_swiper()
        return configurator_page.ConfiguratorPage(self.page, self.base_url).wait_loaded()
