from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

from playwright.sync_api import Page, expect

LoadState = Literal["domcontentloaded", "load", "networkidle"]


class BasePage:
    DEFAULT_TIMEOUT = 30_000

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def open(self, path: str = "", *, wait_until: LoadState = "domcontentloaded") -> Self:
        url = f"{self.base_url}{path}"
        self.page.goto(url, wait_until=wait_until, timeout=self.DEFAULT_TIMEOUT)
        return self

    def reload(self, *, wait_until: LoadState = "domcontentloaded") -> Self:
        self.page.reload(wait_until=wait_until, timeout=self.DEFAULT_TIMEOUT)
        return self

    def wait_loaded(
        self,
        *,
        state: LoadState = "domcontentloaded",
        timeout: int | None = None,
    ) -> Self:
        self.page.wait_for_load_state(state, timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def assert_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(f"*{fragment}*")

    def assert_url_is(self, path: str) -> None:
        expect(self.page).to_have_url(f"{self.base_url}{path}")

    def screenshot(self, name: str, *, folder: str = "artifacts", full_page: bool = True) -> Path:
        Path(folder).mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
        out = Path(folder) / f"{safe_name}.png"
        self.page.screenshot(path=str(out), full_page=full_page)
        return out

    def sleep(self, ms: int) -> Self:
        if ms < 0:
            raise ValueError("ms must be >= 0")
        self.page.wait_for_timeout(ms)
        return self
