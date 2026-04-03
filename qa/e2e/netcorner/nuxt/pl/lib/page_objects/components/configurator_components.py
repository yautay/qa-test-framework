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
        super().__init__(root, name="Sekcja komponentów konfiguratora")

        # locators (private)
        self.__container = root

        self.__tile_cpu = self.__container.locator("[data-name=procesor]").locator("button")
        self.__tile_gpu = self.__container.locator("[data-name=karta-graficzna]").locator("button")
        self.__tile_motherboard = self.__container.locator("[data-name=pyta-gwna]").locator("button")
        self.__tile_ram = self.__container.locator("[data-name=pami-ram]").locator("button")
        self.__tile_drive = self.__container.locator("[data-name=dysk]").locator("button")
        self.__tile_psu = self.__container.locator("[data-name=zasilacz]").locator("button")
        self.__tile_case = self.__container.locator("[data-name=obudowa]").locator("button")

    # actions
    @step("Wybieram kafelek komponentu: Procesor")
    def open_cpu(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_cpu)
        return self

    @step("Wybieram kafelek komponentu: Karta graficzna")
    def open_gpu(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_gpu)
        return self

    @step("Wybieram kafelek komponentu: Płyta główna")
    def open_motherboard(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_motherboard)
        return self

    @step("Wybieram kafelek komponentu: Pamięć RAM")
    def open_ram(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_ram)
        return self

    @step("Wybieram kafelek komponentu: Dysk")
    def open_drive(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_drive)
        return self

    @step("Wybieram kafelek komponentu: Zasilacz")
    def open_psu(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_psu)
        return self

    @step("Wybieram kafelek komponentu: Obudowa")
    def open_case(self) -> ConfiguratorComponentsComponent:
        self.safe_click(self.__tile_case)
        return self


class ConfiguratorAuxComponentsComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Aux Components")


class ConfiguratorSummaryComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Summary Component")
