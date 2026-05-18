from __future__ import annotations

from typing import Self

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.header_actions_component import HeaderActionsComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.header_component import HeaderComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.search_bar_component import SearchBarComponent


class HeaderSection(BaseComponent):
    def __init__(self, page: Page):
        self.__header_root = HeaderComponent(page)
        super().__init__(self.__header_root.root, name="Header Section")
        self.__search_bar: SearchBarComponent | None = None
        self.__actions: HeaderActionsComponent | None = None

        # layout locators (scoped inside [data-name='headerBar'])
        self.__logo = self.find("img[data-name='logo']")
        self.__help_contact = self.find("a[aria-label='Kontakt i pomoc']")
        self.__search_where = self.find("[data-name='searchCategoryWrapper']")

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

    # --- layout assertions ---

    @step("Sprawdzam widoczność logo")
    def expect_logo_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__logo).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność linku 'Kontakt i pomoc'")
    def expect_help_contact_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__help_contact).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność dropdown 'gdzie szukasz'")
    def expect_search_where_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__search_where).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam, że dropdown wyszukiwania domyślnie pokazuje 'wszędzie'")
    def assert_search_where_default(self) -> Self:
        expect(self.__search_where).to_contain_text("wszędzie", timeout=self.DEFAULT_TIMEOUT)
        return self

    @step("Klikam dropdown wyszukiwania i sprawdzam, że opcje są widoczne")
    def expect_search_where_has_options(self, timeout_ms: int = 10_000) -> Self:
        self.pointer_click(self.__search_where)
        # After click the categories list renders dynamically
        # selector from Selenium: [data-name='searchCategories']
        options = self.find("[data-name='searchCategories']")
        expect(options).to_be_visible(timeout=timeout_ms)
        return self
