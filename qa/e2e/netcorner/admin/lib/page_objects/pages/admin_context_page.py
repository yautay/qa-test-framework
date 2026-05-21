from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState
from qa.e2e.netcorner.admin.lib.timeouts import UI_ACTION_MS


class AdminContextPage(AdminBasePage):
    """Sales channel context selector — shown once after login.

    URL: <admin_base_url>/admin.php  (redirected here after login)
    Confirmed live — admin shows:
        <h1>Proszę wybrać kanał sprzedaży w ramach którego będziesz pracował</h1>
        <select name="sales_channel_id" id="sales_channel_id">
            <option value="1">komputronik.pl</option>
            ...
        <input class="sf_admin_action_save" type="submit" />

    Known sales_channel_id values (from live HTML, 2026-05-14):
        1  → komputronik.pl  (PL — default for nuxt/pl tests)
        9  → k24.cz
        10 → k24.sk
        15 → d.ktr.pl
        16 → biznes.ktr.pl
        31 → k24.ktr.pl
        64 → b2b.komputronik.eu
    """

    PAGE_ID = "netcorner.admin.context"

    _LOC_CONTEXT_HEADER = "h1:has-text('Proszę wybrać kanał sprzedaży')"
    _LOC_SALES_CHANNEL_SELECT = "select#sales_channel_id"
    _LOC_SAVE_BUTTON = "input.sf_admin_action_save"
    # After context is chosen the admin main container appears
    _LOC_ADMIN_CONTAINER = "#sf_admin_container"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminContextPage:
        super().wait_loaded(state=state, timeout=timeout)
        return self

    def is_context_selection_required(self) -> bool:
        """Returns True if the context selector is displayed (not yet chosen).

        Uses the select element as the primary signal — it is more reliably
        present than the H1 which may not yet be in the DOM when this is called
        immediately after login completes (domcontentloaded fires before the
        server-rendered H1 is stable in some environments).
        """
        return self.page.locator(self._LOC_SALES_CHANNEL_SELECT).is_visible(timeout=UI_ACTION_MS)

    def select_context(self, sales_channel_id: int) -> None:
        """Choose a sales channel and save. After this the admin main page is loaded."""
        select = self.page.locator(self._LOC_SALES_CHANNEL_SELECT)
        select.select_option(value=str(sales_channel_id))
        self.page.locator(self._LOC_SAVE_BUTTON).click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.locator(self._LOC_ADMIN_CONTAINER).wait_for(state="visible", timeout=UI_ACTION_MS)


__all__ = ["AdminContextPage"]
