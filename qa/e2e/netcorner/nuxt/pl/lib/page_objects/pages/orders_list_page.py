from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.orders_list_component import (
    OrderRowComponent,
    OrderRowData,
    OrdersListComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer_section import FooterSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.header_section import HeaderSection
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation_section import NavigationSection


class OrdersListPage(BasePage):
    """Customer account — orders list page.

    URL: ``/customer/account/orders``

    The page renders a SPA list of orders; content hydrates after ``domcontentloaded``.
    ``wait_loaded()`` waits for at least the page chrome (header/nav) but does NOT block
    on the orders list itself — call ``content.wait_orders_loaded()`` explicitly when you
    need list items to be present.
    """

    PATH = "/customer/account/orders"
    PAGE_ID = "netcorner.pl.account.orders_list"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__content: OrdersListComponent | None = None
        self.__header: HeaderSection | None = None
        self.__navigation: NavigationSection | None = None
        self.__footer: FooterSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> OrdersListPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
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
    def content(self) -> OrdersListComponent:
        if self.__content is None:
            self.__content = OrdersListComponent(self.page)
        return self.__content

    @property
    def footer(self) -> FooterSection:
        if self.__footer is None:
            self.__footer = FooterSection(self.page)
        return self.__footer

    def open_and_wait_orders(self) -> OrdersListPage:
        """Open the orders page and wait for the list to hydrate."""
        self.open(self.PATH).wait_loaded()
        self.content.wait_orders_loaded()
        return self

    def find_order(self, order_number: str) -> OrderRowComponent | None:
        return self.content.find_order_by_number(order_number)

    def get_first_order_data(self) -> OrderRowData:
        return self.content.row(0).get_data()
