from __future__ import annotations

from framework.base.page_objects import BasePage as FrameworkBasePage
from framework.base.page_objects import LoadState
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays


class BasePage(FrameworkBasePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._overlays = None

    @property
    def overlays(self):
        if self._overlays is None:
            self._overlays = Overlays(self.page)
        return self._overlays


__all__ = ["BasePage", "LoadState"]
