from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.navigation_component import NavigationComponent


class NavigationSection(NavigationComponent):
    def __init__(self, page: Page):
        super().__init__(page)
