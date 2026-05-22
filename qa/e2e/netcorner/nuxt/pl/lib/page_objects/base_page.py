from __future__ import annotations

from framework.base.page_objects import BasePage as FrameworkBasePage
from framework.base.page_objects import LoadState
from qa.e2e.netcorner.lib.dom_capture import capture_page_dom
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.timeouts import UI_ACTION_MS


class BasePage(FrameworkBasePage):
    PAGE_ID = "netcorner.pl.page.unknown"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._overlays = None

    def _wait_for_nuxt_hydration(self, timeout: int = UI_ACTION_MS) -> None:
        """Wait until Nuxt client-side hydration is complete.

        After ``domcontentloaded`` the page is static SSR HTML — Vue event
        handlers are not yet registered.  Hydration is complete when
        ``window.useNuxtApp().isHydrating`` returns ``false``.

        If ``useNuxtApp`` is not available (non-Nuxt page, SSR-only route) the
        wait is skipped silently — the guard is intentionally lenient only for
        the *absence* of the Nuxt runtime, not for hydration timeout.

        Raises:
            playwright.sync_api.TimeoutError: when ``useNuxtApp`` exists but
                hydration does not finish within ``timeout`` ms.
        """
        self.page.wait_for_function(
            """() => {
                if (typeof window.useNuxtApp !== 'function') return true;
                try {
                    return window.useNuxtApp().isHydrating === false;
                } catch (e) {
                    return false;
                }
            }""",
            timeout=timeout,
        )

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None):
        super().wait_loaded(state=state, timeout=timeout)
        self._wait_for_nuxt_hydration()
        return self

    def capture_dom_snapshot(self, *, event: str = "page_loaded") -> None:
        capture_page_dom(self.page, event=event, page_id=self.PAGE_ID)

    @property
    def overlays(self):
        if self._overlays is None:
            self._overlays = Overlays(self.page)
        return self._overlays


__all__ = ["BasePage", "LoadState"]
