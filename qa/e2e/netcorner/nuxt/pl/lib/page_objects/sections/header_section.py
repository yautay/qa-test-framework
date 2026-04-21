from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.header_component import HeaderComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.header_actions_component import HeaderActionsComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.search_bar_component import SearchBarComponent


class HeaderSection(BaseComponent):
    def __init__(self, page: Page):
        self.__header_root = HeaderComponent(page)
        super().__init__(self.__header_root.root, name="Header Section")
        self.__search_bar: SearchBarComponent | None = None
        self.__actions: HeaderActionsComponent | None = None

    @property
    def search_bar(self) -> SearchBarComponent:
        if self.__search_bar is None:
            self.__search_bar = SearchBarComponent(self.root)
        return self.__search_bar

    @property
    def actions(self) -> HeaderActionsComponent:
        if self.__actions is None:
            self.__actions = HeaderActionsComponent(self.root)
        return self.__actions
