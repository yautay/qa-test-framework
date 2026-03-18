from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.login_overlay import LoginOverlay
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.toast_overlay import ToastOverlay


class Overlays:
    def __init__(self, page: Page):
        self.page = page
        self.__login: LoginOverlay | None = None
        self.__toast: ToastOverlay | None = None

    @property
    def login(self) -> LoginOverlay:
        if self.__login is None:
            self.__login = LoginOverlay(self.page)
        return self.__login

    @property
    def password_recovery(self) -> LoginOverlay:
        if self.__login is None:
            self.__login = LoginOverlay(self.page)
        return self.__login

    @property
    def toast(self) -> ToastOverlay:
        if self.__toast is None:
            self.__toast = ToastOverlay(self.page)
        return self.__toast
