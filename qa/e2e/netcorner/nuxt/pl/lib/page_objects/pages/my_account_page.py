from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages import home_page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content_section import MyAccountContentSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer_section import FooterSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.header_section import HeaderSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import NavigationSection


class MyAccountPage(BasePage):
    PATH = "/customer/account"
    PAGE_ID = "netcorner.pl.account.main"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: MyAccountContentSection | None = None
        self.__navigation: NavigationSection | None = None
        self.__header: HeaderSection | None = None
        self.__footer: FooterSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> MyAccountPage:
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
    def content(self) -> MyAccountContentSection:
        if self.__content is None:
            self.__content = MyAccountContentSection(self.page)
        return self.__content

    @property
    def footer(self) -> FooterSection:
        if self.__footer is None:
            self.__footer = FooterSection(self.page)
        return self.__footer

    def open_login_overlay(self):
        self.header.actions.open_login()
        return self.overlays.login.wait_visible()

    def open_account_page(self) -> MyAccountPage:
        self.header.actions.open_account()
        return MyAccountPage(self.page, self.base_url).wait_loaded()

    def open_orders_page(self) -> "OrdersListPage":
        from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.orders_list_page import OrdersListPage

        self.content.menu_root.open_orders()
        return OrdersListPage(self.page, self.base_url).wait_loaded()

    def open_password_change_page(self) -> MyAccountChangePasswordPage:
        self.content.menu_root.open_password_change()
        return MyAccountChangePasswordPage(self.page, self.base_url).wait_loaded()

    def logout_to_home_page(self) -> home_page.HomePage:
        self.content.menu_root.logout()
        return home_page.HomePage(self.page, self.base_url).wait_loaded()


class MyAccountChangePasswordPage(MyAccountPage):
    PATH = "/customer/account/password-change"
    PAGE_ID = "netcorner.pl.account.password_change"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: MyAccountContentSection | None = None
        self.__navigation: NavigationSection | None = None
        self.__header: HeaderSection | None = None
        self.__footer: FooterSection | None = None

    def wait_loaded(
        self,
        *,
        state: LoadState = "domcontentloaded",
        timeout: int | None = None,
    ) -> MyAccountChangePasswordPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.capture_dom_snapshot(event="page_loaded")
        return self
