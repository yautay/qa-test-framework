from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.login_overlay import LoginOverlay


class Overlays:
    def __init__(self, page: Page):
        self.page = page
        self.login = LoginOverlay(page)

    def dismiss_blockers(self) -> None:
        pass
