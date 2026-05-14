from __future__ import annotations

from framework.base.page_objects import BasePage as FrameworkBasePage
from framework.base.page_objects import LoadState


class AdminBasePage(FrameworkBasePage):
    """Base class for all admin panel pages.

    The admin panel is a classic server-rendered Symfony app (not a SPA).
    It uses `id=` attributes extensively — prefer those as root selectors.
    `ignore_https_errors` must be True (internal CA, not in system trust store).
    """

    PAGE_ID = "netcorner.admin.page.unknown"
    # Admin base path appended to base_url when opening
    ADMIN_PATH = "/admin.php"

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminBasePage:
        return super().wait_loaded(state=state, timeout=timeout)


__all__ = ["AdminBasePage", "LoadState"]
