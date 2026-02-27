from __future__ import annotations

from playwright.sync_api import Locator
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class HeaderActionsComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Header Actions")
        self.__login = self.find('[data-name="loginDialogTrigger"]')
        self.__cart = self.find('[data-name="miniCartWrapper"]')
        self.__my_account = self.find('[href="/customer/account/"]')

    def open_login(self) -> None:
        self.safe_click(self.__login)

    def open_account(self) -> None:
        self.safe_click(self.__my_account)

    def open_cart(self) -> None:
        self.safe_click(self.__cart)

    def is_my_account_available(self) -> bool:
        return self.__my_account.is_visible(timeout=3000)