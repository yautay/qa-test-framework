from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class CartComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='configuratorActions']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Configuration Actions Component")



class CartSummaryComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='configuratorGrid']"

