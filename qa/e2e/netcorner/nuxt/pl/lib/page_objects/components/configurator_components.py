from __future__ import annotations

from playwright.sync_api import Locator

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class ConfiguratorActionsComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configuration Actions Component")

        # locators (private)
        self.__container = root
        self.__text_configuration_name = self.__container.get_by_text("Nazwa konfiguracji", exact=True)
        self.__button_clear = self.__container.get_by_role("button", name="Wyczyść", exact=True)
        self.__button_create_copy = self.__container.get_by_role("button", name="Stwórz kopię", exact=True)
        self.__button_share = self.__container.get_by_role("button", name="Udostępnij", exact=True)

    # actions
    @step("Czyszczę konfigurację")
    def clear_configuration(self) -> None:
        self.safe_click(self.__button_clear)

    @step("Tworzę kopię konfiguracji")
    def create_copy(self) -> None:
        self.safe_click(self.__button_create_copy)

    @step("Udostępniam konfigurację")
    def share_configuration(self) -> ConfiguratorActionsComponent:
        self.safe_click(self.__button_share)
        return self

    # getters
    @step("Pobieram nagłówek sekcji konfiguracji")
    def get_configuration_section_title(self) -> str:
        return (self.__text_configuration_name.text_content() or "").strip()


class ConfiguratorComponentsComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configuration Components Component")

        # locators (private)
        self.__grid_components = self.find(
            "css=div.grid.grid-cols-1.gap-6.md\\:auto-rows-fr.md\\:grid-cols-2.xl\\:grid-cols-3.2xl\\:grid-cols-4"
        )


class ConfiguratorAuxComponentsComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Aux Components")


class ConfiguratorSummaryComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Summary Component")
