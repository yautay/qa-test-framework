from __future__ import annotations

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState
from qa.e2e.netcorner.admin.lib.timeouts import UI_ACTION_MS


class AdminConfigurationPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.configuration.list"
    PATH = "/admin.php/configuration/list/pl#"

    _LOC_CONTAINER = "#sf_admin_container"
    _LOC_POSTCODES_SECTION = "a:has-text('Wymuszenie ścieżki zakupowej z listą metod transportu')"
    _LOC_POSTCODES_TEXTAREA = "#enforce_shopping_path_post_codes"
    _LOC_POSTCODES_SAVE = "span#enforce_shopping_path_post_codes1 input[type='button']"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def navigate_to(self) -> AdminConfigurationPage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminConfigurationPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.page.locator(self._LOC_CONTAINER).wait_for(state="visible", timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def open_enforced_postcodes_section(self) -> None:
        self.page.locator(self._LOC_POSTCODES_SECTION).click()
        expect(self.page.locator(self._LOC_POSTCODES_TEXTAREA)).to_be_visible(timeout=UI_ACTION_MS)

    def get_enforced_postcodes(self) -> list[str]:
        self.open_enforced_postcodes_section()
        raw = (self.page.locator(self._LOC_POSTCODES_TEXTAREA).input_value() or "").strip()
        if not raw:
            return []
        return [value.strip() for value in raw.split(",") if value.strip()]

    def set_enforced_postcodes(self, postcodes: list[str]) -> None:
        self.open_enforced_postcodes_section()
        normalized = ",".join(dict.fromkeys(value.strip() for value in postcodes if value.strip()))
        textarea = self.page.locator(self._LOC_POSTCODES_TEXTAREA)
        textarea.fill(normalized)
        self.page.locator(self._LOC_POSTCODES_SAVE).click()
        expect(textarea).to_have_value(normalized, timeout=UI_ACTION_MS)


__all__ = ["AdminConfigurationPage"]
