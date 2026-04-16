from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent


class FooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="footer"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Footer Component")
