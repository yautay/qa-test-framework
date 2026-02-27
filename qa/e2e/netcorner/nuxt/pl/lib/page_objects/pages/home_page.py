from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_page import BasePage, LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.content import Content
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.footer import Footer
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.header import Header
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.sections.navigation import Navigation


class HomePage(BasePage):
    PATH = "/"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self._content: Content | None = None
        self._header: Header | None = None
        self._navigation: Navigation | None = None
        self._footer: Footer | None = None

    def wait_loaded(
        self,
        *,
        state: LoadState = "domcontentloaded",
        timeout: int | None = None,
    ) -> "HomePage":
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
        self.navigation.wait_visible()
        self.content.wait_visible()
        self.footer.wait_visible()
        return self

    @property
    def header(self) -> Header:
        if self._header is None:
            self._header = Header(self.page)
        return self._header

    @property
    def navigation(self) -> Navigation:
        if self._navigation is None:
            self._navigation = Navigation(self.page)
        return self._navigation

    @property
    def content(self) -> Content:
        if self._content is None:
            self._content = Content(self.page)
        return self._content

    @property
    def footer(self) -> Footer:
        if self._footer is None:
            self._footer = Footer(self.page)
        return self._footer
