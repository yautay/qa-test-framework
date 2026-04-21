from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class ContentRootComponent(BaseComponent):
    ROOT_SELECTOR = "#pageContentWrapper"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Content Root Component")
