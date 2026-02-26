from __future__ import annotations

from playwright.sync_api import Page, Locator
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class Footer(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="footer"]'), name="Footer Section")
