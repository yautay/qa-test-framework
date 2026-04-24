from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class FooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="footer"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Footer Component")


class CartFooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="cartFooter"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Cart Footer Component")

        self.__btn_continue = self.root.get_by_role("button", name="Przejdź dalej").first
        self.__btn_clear_cart = self.root.get_by_role("button", name="Wyczyść koszyk").first
        self.__btn_back_to_shopping = self.root.get_by_role("button", name="Wróć do zakupów").first
        self.__btn_copy_link = self.root.get_by_text("Skopiuj link").first

    # actions
    @step("Klikam 'Przejdź dalej'")
    def click_continue(self) -> None:
        self.pointer_click(self.__btn_continue)

    @step("Klikam 'Wyczyść koszyk'")
    def click_clear_cart(self) -> None:
        self.pointer_click(self.__btn_clear_cart)

    @step("Klikam 'Wróć do zakupów'")
    def click_back_to_shopping(self) -> None:
        self.pointer_click(self.__btn_back_to_shopping)

    @step("Klikam 'Skopiuj link'")
    def click_copy_link(self) -> None:
        self.pointer_click(self.__btn_copy_link)
