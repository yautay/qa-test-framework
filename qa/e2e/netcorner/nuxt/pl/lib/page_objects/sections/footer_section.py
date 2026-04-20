from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.footer_component import FooterComponent


class FooterSection(FooterComponent):
    def __init__(self, page: Page):
        super().__init__(page)

class CartFooterSection(CartFooterComponent):
    def __init__(self, page: Page):
        super().__init__(page)