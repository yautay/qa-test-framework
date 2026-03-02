from __future__ import annotations

from playwright.sync_api import Page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.search_bar_component import SearchBarComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.header_actions_component import HeaderActionsComponent


class HeaderSection(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="headerBar"]'), name="Header Section")
        self.__search_bar: SearchBarComponent | None = None
        self.__actions: HeaderActionsComponent | None = None

    @property
    def search_bar(self) -> SearchBarComponent:
        if self.__search_bar is None:
            self.__search_bar = SearchBarComponent(self.find('[data-role="searchComponent"]'))
        return self.__search_bar

    @property
    def actions(self) -> HeaderActionsComponent:
        if self.__actions is None:
            self.__actions = HeaderActionsComponent(self.find('[data-name="headerActions"]'))
        return self.__actions