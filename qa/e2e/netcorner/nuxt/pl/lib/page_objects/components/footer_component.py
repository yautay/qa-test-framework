from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.lib.step_api import step


class FooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="footer"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Footer Component")

class CartFooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="cartFooter"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Cart Footer Component")

        self.__btn_continue = self.find("role=button[name='Przejdź dalej']")
        self.__btn_clear_cart = self.find("role=button[name='Wyczyść koszyk']")
        self.__btn_back_to_shopping = self.find("role=button[name='Wróć do zakupów']")
        self.__btn_copy_link = self.find("text=Skopiuj link")

    # actions
    @step("Klikam 'Przejdź dalej'")
    def click_continue(self) -> None:
        self.safe_click(self.__btn_continue)

    @step("Klikam 'Wyczyść koszyk'")
    def click_clear_cart(self) -> None:
        self.safe_click(self.__btn_clear_cart)

    @step("Klikam 'Wróć do zakupów'")
    def click_back_to_shopping(self) -> None:
        self.safe_click(self.__btn_back_to_shopping)

    @step("Klikam 'Skopiuj link'")
    def click_copy_link(self) -> None:
        self.safe_click(self.__btn_copy_link)
