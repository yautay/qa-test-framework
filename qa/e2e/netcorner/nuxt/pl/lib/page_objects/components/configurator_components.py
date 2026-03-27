from __future__ import annotations

from playwright.sync_api import Locator

from framework.base.page_objects import BaseComponent


class ConfiguratorRootComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Root Component")


class ConfiguratorAdviseComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Advise Component")


class ConfiguratorComponentsListComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Components List Component")


class ConfiguratorSummaryComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Configurator Summary Component")
