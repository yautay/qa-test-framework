from __future__ import annotations

from playwright.sync_api import Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.configurator_components import (
    ConfiguratorAuxComponentsComponent, ConfiguratorComponentsComponent, ConfiguratorSummaryComponent,
    ConfiguratorActionsComponent
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.hero_component import HeroComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.my_account_component import (
    MyAccountComponent,
    MyAccountPasswordChangeComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.password_recovery_component import PasswordRecoveryComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.register_client_component import RegisterClientComponent


class ContentSection(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator("#pageContentWrapper"), name="Content Section")


class PasswordRecoveryContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__password_recovery: PasswordRecoveryComponent | None = None

    @property
    def recovery_form(self) -> PasswordRecoveryComponent:
        if self.__password_recovery is None:
            self.__password_recovery = PasswordRecoveryComponent(self.root.locator("[data-name='passwordResetPage']"))
        return self.__password_recovery


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


class HeroPageContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__hero: HeroComponent | None = None

    @property
    def hero(self) -> HeroComponent:
        if self.__hero is None:
            self.__hero = HeroComponent(self.root.locator("#pageContent"))
        return self.__hero


class ConfiguratorContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__set_actions: ConfiguratorActionsComponent | None = None
        self.__components: ConfiguratorComponentsComponent | None = None
        self.__components_aux: ConfiguratorAuxComponentsComponent | None = None
        self.__summary: ConfiguratorSummaryComponent | None = None

    @property
    def actions(self) -> ConfiguratorActionsComponent:
        if self.__set_actions is None:
            self.__set_actions = ConfiguratorActionsComponent(self.root.locator('//div[@data-name="configuratorHead"]/../..'))
        return self.__set_actions

    @property
    def components(self) -> ConfiguratorComponentsComponent:
        if self.__components is None:
            self.__components = ConfiguratorComponentsComponent(self.root.locator("#komputronik-advise"))
        return self.__components

    @property
    def aux_components(self) -> ConfiguratorAuxComponentsComponent:
        if self.__components_aux is None:
            self.__components_aux = ConfiguratorAuxComponentsComponent(self.root.locator("[data-name='app-content']"))
        return self.__components_aux

    @property
    def summary(self) -> ConfiguratorSummaryComponent:
        if self.__summary is None:
            self.__summary = ConfiguratorSummaryComponent(self.root.locator("div.max-body-w.bg-gray-porcelain"))
        return self.__summary
