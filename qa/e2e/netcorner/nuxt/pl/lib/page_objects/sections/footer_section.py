from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class FooterSection(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="footer"]'), name="Footer Section")
