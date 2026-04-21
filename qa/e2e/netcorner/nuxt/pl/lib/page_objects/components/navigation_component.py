from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.lib.step_api import step


class NavigationComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="navigationBar"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Navigation Component")


class CheckoutNavigationComponent(BaseComponent):
    ROOT_SELECTOR = '[data-role="order-stepper"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Cart Navigation Component")

        self.__back_to_shopping_link = self.find("a:has-text('Wróć do zakupów')")
        self.__step_1 = self.find("[data-step='1']")
        self.__step_2 = self.find("[data-step='2']")
        self.__step_3 = self.find("[data-step='3']")
        self.__step_4 = self.find("[data-step='4']")

    def __get_step_locator(self, step: int) -> Locator:
        if step == 1:
            return self.__step_1
        if step == 2:
            return self.__step_2
        if step == 3:
            return self.__step_3
        if step == 4:
            return self.__step_4
        raise ValueError(f"Unsupported step: {step}")

    def __click_step(self, step: int) -> None:
        step_locator = self.__get_step_locator(step).first
        if step_locator.count() == 0 or not step_locator.is_visible():
            raise AssertionError(f"Step {step} is not visible")

        tag_name = (step_locator.evaluate("el => el.tagName") or "").lower()
        if tag_name != "a":
            raise AssertionError(f"Step {step} is not clickable in current state")

        self.safe_click(step_locator)

    @step("Klikam 'Wróć do zakupów'")
    def click_back_to_shopping(self) -> None:
        self.safe_click(self.__back_to_shopping_link)

    @step("Klikam krok 1")
    def click_step_1(self) -> None:
        self.__click_step(1)

    @step("Klikam krok 2")
    def click_step_2(self) -> None:
        self.__click_step(2)

    @step("Klikam krok 3")
    def click_step_3(self) -> None:
        self.__click_step(3)

    @step("Klikam krok 4")
    def click_step_4(self) -> None:
        self.__click_step(4)

    @step("Pobieram bieżący krok zamówienia")
    def get_current_step(self) -> int:
        raw = (self.root.get_attribute("data-current-step") or "").strip()
        try:
            return int(raw)
        except ValueError:
            return 0
