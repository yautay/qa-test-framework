from __future__ import annotations

from pathlib import Path
from typing import Literal

from playwright.sync_api import Page, expect
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays

LoadState = Literal["domcontentloaded", "load", "networkidle"]


class BasePage:
    DEFAULT_TIMEOUT = 3_000

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self._overlays = None

    @property
    def overlays(self):
        if self._overlays is None:
            self._overlays = Overlays(self.page)
        return self._overlays

    # ---------- navigation ----------
    def open(self, path: str = "", *, wait_until: LoadState = "domcontentloaded") -> "BasePage":
        url = f"{self.base_url}{path}"
        self.page.goto(url, wait_until=wait_until, timeout=self.DEFAULT_TIMEOUT)
        return self

    def reload(self, *, wait_until: LoadState = "domcontentloaded") -> "BasePage":
        self.page.reload(wait_until=wait_until, timeout=self.DEFAULT_TIMEOUT)
        return self

    # ---------- state ----------
    def wait_loaded(
        self,
        *,
        state: LoadState = "domcontentloaded",
        timeout: int | None = None,
    ) -> "BasePage":
        self.page.wait_for_load_state(state, timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def assert_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(f"*{fragment}*")

    def assert_url_is(self, path: str) -> None:
        # path np. "/customer/account/"
        expect(self.page).to_have_url(f"{self.base_url}{path}")

    # ---------- debug ----------
    def screenshot(self, name: str, *, folder: str = "artifacts", full_page: bool = True) -> Path:
        Path(folder).mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
        out = Path(folder) / f"{safe_name}.png"
        self.page.screenshot(path=str(out), full_page=full_page)
        return out
