from __future__ import annotations

from playwright.sync_api import Locator
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class HeaderActions(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Header Actions")
        self._login = self.find('[data-name="loginDialogTrigger"]')
        self._cart = self.find('[data-name="miniCartWrapper"]')
        self._my_account = self.find('[href="/customer/account/"]')

    def open_login(self) -> None:
        self.safe_click(self._login)

    def open_account(self) -> None:
        self.safe_click(self._my_account)

    def open_cart(self) -> None:
        self.safe_click(self._cart)

    def is_my_account_available(self) -> bool:
        return self._my_account.is_visible(timeout=3000)
