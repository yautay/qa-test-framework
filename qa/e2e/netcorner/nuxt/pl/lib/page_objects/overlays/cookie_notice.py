from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PwTimeoutError


class CookieNotice:
    """
    Universal cookie banner handler.
    - Does not raise an exception if the banner is not present.
    - Uses short timeouts to avoid slowing down tests.
    """

    def __init__(self, page: Page):
        self.page = page
        self.root = page.locator('#onetrust-banner-sdk, #onetrust-consent-sdk, [aria-label="Cookie banner"]')
        self.accept = page.locator(
            '#onetrust-accept-btn-handler, button:has-text("Zgadzam"), '
            'button:has-text("Zaakceptuj"), button:has-text("I agree")'
        )

    def dismiss_if_present(self) -> None:
        try:
            if self.root.first.is_visible():
                self.accept.first.click(timeout=2000)
        except PwTimeoutError:
            return
        except Exception:
            return
