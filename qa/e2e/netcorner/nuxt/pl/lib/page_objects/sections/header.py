from __future__ import annotations

from playwright.sync_api import Page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.search_bar import SearchBar
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.header_actions import HeaderActions


class Header(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="headerBar"]'), name="Header Section")
        self._search_bar: SearchBar | None = None
        self._actions: HeaderActions | None = None

    @property
    def search_bar(self) -> SearchBar:
        if self._search_bar is None:
            self._search_bar = SearchBar(self.find('[data-role="searchComponent"]'))
        return self._search_bar

    @property
    def actions(self) -> HeaderActions:
        if self._actions is None:
            self._actions = HeaderActions(self.find('[data-name="headerActions"]'))
        return self._actions