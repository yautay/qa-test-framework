from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class ComparisonComponent(BaseComponent):
    def __init__(self, scope: Page | Locator) -> None:
        root = scope if isinstance(scope, Locator) else scope.locator("body")
        super().__init__(root, name="Comparison Component")
        self.__compare_action = self.find("[data-name='productAction'][title='Porównaj']").first

    @step("Sprawdzam dostępność akcji 'Porównaj'")
    def is_compare_action_visible(self) -> bool:
        return self.__compare_action.count() > 0 and self.__compare_action.is_visible()
