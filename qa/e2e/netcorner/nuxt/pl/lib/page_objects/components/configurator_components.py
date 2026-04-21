from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class ConfiguratorActionsComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='configuratorActions']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Configuration Actions Component")

        # locators (private)
        self.__container = self.root
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
    ROOT_SELECTOR = "[data-name='configuratorGrid']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Sekcja komponentów konfiguratora")

        # locators (private)
        self.__container = self.root

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
    ROOT_SELECTOR = "[data-name='configuratorGridOptionalElements']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Configurator Aux Components")


class ConfiguratorSummaryComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='configuratorFooter']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Configurator Summary Component")
