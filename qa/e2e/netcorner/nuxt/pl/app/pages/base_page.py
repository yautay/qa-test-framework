from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Locator, Page, TimeoutError, expect

from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import CookieSelectors


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.context: BrowserContext = page.context
        self.browser: Browser | None = page.context.browser

    def locator(self, selector: str) -> Locator:
        if selector.startswith("//"):
            return self.page.locator(f"xpath={selector}")
        return self.page.locator(selector)

    def click(self, selector: str) -> None:
        self.locator(selector).click()

    def fill(self, selector: str, value: str) -> None:
        self.locator(selector).fill(value)

    def expect_visible(self, selector: str) -> None:
        expect(self.locator(selector)).to_be_visible()

    def click_first_visible(self, selectors: list[str], timeout: int = 3000) -> bool:
        for selector in selectors:
            candidate = self.locator(selector)
            count = candidate.count()
            if count == 0:
                continue
            for idx in range(min(count, 10)):
                target = candidate.nth(idx)
                try:
                    target.click(timeout=timeout)
                    return True
                except Exception:
                    continue
        return False

    def fill_first_visible(self, selectors: list[str], value: str, timeout: int = 3000) -> bool:
        for selector in selectors:
            candidate = self.locator(selector)
            count = candidate.count()
            if count == 0:
                continue
            for idx in range(min(count, 10)):
                target = candidate.nth(idx)
                try:
                    target.fill(value, timeout=timeout)
                    return True
                except Exception:
                    continue
        return False

    def any_visible(self, selectors: list[str], timeout_ms: int = 2500) -> bool:
        for selector in selectors:
            candidate = self.locator(selector)
            count = candidate.count()
            if count == 0:
                continue
            for idx in range(min(count, 10)):
                try:
                    candidate.nth(idx).wait_for(state="visible", timeout=timeout_ms)
                    return True
                except TimeoutError:
                    continue
                except Exception:
                    continue
        return False

    def dismiss_cookie_banner(self) -> None:
        self.click_first_visible(CookieSelectors.ACCEPT_BUTTONS, timeout=1200)
        self.click_first_visible(CookieSelectors.REJECT_BUTTONS, timeout=800)
        try:
            overlay = self.locator(CookieSelectors.OVERLAY)
            if overlay.count() > 0 and overlay.first.is_visible():
                self.page.evaluate("""
                    () => {
                        const el = document.querySelector('#onetrust-consent-sdk');
                        if (el) {
                            el.remove();
                        }
                    }
                    """)
        except Exception:
            return
