from __future__ import annotations

from playwright.sync_api import Page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.register_client import RegisterClient


class Content(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('#pageContent'), name="Content Section")


class RegisterContent(Content):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._register_client: RegisterClient | None = None

    @property
    def register_form(self) -> RegisterClient:
        if self._register_client is None:
            self._register_client = RegisterClient(self.root.locator("form"))
        return self._register_client