from __future__ import annotations

from framework.base.page_objects import BasePage as FrameworkBasePage
from framework.base.page_objects import LoadState
from qa.e2e.netcorner.lib.dom_capture import capture_page_dom
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays


class BasePage(FrameworkBasePage):
    PAGE_ID = "netcorner.pl.page.unknown"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._overlays = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None):
        return super().wait_loaded(state=state, timeout=timeout)

    def capture_dom_snapshot(self, *, event: str = "page_loaded") -> None:
        capture_page_dom(self.page, event=event, page_id=self.PAGE_ID)

    @property
    def overlays(self):
        if self._overlays is None:
            self._overlays = Overlays(self.page)
        return self._overlays


__all__ = ["BasePage", "LoadState"]
