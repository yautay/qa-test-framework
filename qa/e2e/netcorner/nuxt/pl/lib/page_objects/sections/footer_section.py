from __future__ import annotations

from playwright.sync_api import Page

from framework.base.page_objects import BaseComponent


class FooterSection(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="footer"]'), name="Footer Section")
