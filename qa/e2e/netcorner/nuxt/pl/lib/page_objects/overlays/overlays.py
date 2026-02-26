from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.cookie_notice import CookieNotice
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.login_overlay import LoginOverlay


class Overlays:
    def __init__(self, page: Page):
        self.page = page
        self.cookie = CookieNotice(page)
        self.login = LoginOverlay(page)

    def dismiss_blockers(self) -> None:
        # wszystko co może blokować klik
        self.cookie.dismiss_if_present()