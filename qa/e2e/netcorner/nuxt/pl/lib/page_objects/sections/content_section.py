from __future__ import annotations

from playwright.sync_api import Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.my_account_component import (
    MyAccountComponent,
    MyAccountPasswordChangeComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.register_client_component import RegisterClientComponent


class ContentSection(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator("#pageContentWrapper"), name="Content Section")


class RegisterContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__register_client: RegisterClientComponent | None = None

    @property
    def register_form(self) -> RegisterClientComponent:
        if self.__register_client is None:
            self.__register_client = RegisterClientComponent(self.root.locator("form"))
        return self.__register_client


class MyAccountContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__my_account: MyAccountComponent | None = None
        self.__my_account_password_change: MyAccountPasswordChangeComponent | None = None

    @property
    def menu_root(self) -> MyAccountComponent:
        if self.__my_account is None:
            self.__my_account = MyAccountComponent(self.root.locator("#pageContent"))
        return self.__my_account

    @property
    def menu_change_password(self) -> MyAccountPasswordChangeComponent:
        if self.__my_account_password_change is None:
            self.__my_account_password_change = MyAccountPasswordChangeComponent(self.root.locator("#pageContent"))
        return self.__my_account_password_change
