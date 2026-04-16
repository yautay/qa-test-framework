from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class HeaderActionsComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="headerActions"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Header Actions")
        self.__login = self.find('[data-name="loginDialogTrigger"]')
        self.__cart = self.find('[data-name="miniCartWrapper"]')
        self.__my_account = self.find('[href="/customer/account/"]')

    @step("Otwieram modal logowania")
    def open_login(self) -> None:
        self.safe_click(self.__login)

    @step("Przechodzę do panelu klienta")
    def open_account(self) -> None:
        self.safe_click(self.__my_account)

    @step("Otwieram mini koszyk")
    def open_cart(self) -> None:
        self.safe_click(self.__cart)

    @step("Sprawdzam dostępność linku do sekcji 'Moje konto'")
    def is_my_account_available(self) -> bool:
        return self.__my_account.is_visible()
