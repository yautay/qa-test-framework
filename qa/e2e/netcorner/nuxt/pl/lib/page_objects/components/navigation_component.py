from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent


class NavigationComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="navigationBar"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Navigation Component")
