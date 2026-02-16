from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import CheckoutSelectors


class CheckoutPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url.rstrip("/")

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/checkout")

    def is_ready(self) -> bool:
        return "/checkout" in self.page.url and self.page.locator("body").first.is_visible()

    def has_interactive_checkout_surface(self) -> bool:
        for selector in CheckoutSelectors.INTERACTIVE_CANDIDATES:
            locator = self.page.locator(selector)
            count = locator.count()
            if count == 0:
                continue
            for idx in range(min(count, 15)):
                if locator.nth(idx).is_visible():
                    return True
        for keyword in CheckoutSelectors.TEXT_CANDIDATES:
            if self.page.get_by_text(keyword, exact=False).first.is_visible():
                return True
        return False

    def select_delivery_kind(self, delivery_kind: str) -> None:
        selector = CheckoutSelectors.DELIVERY_TILES.get(delivery_kind)
        if selector:
            self.click(selector)

    def fill_receiver_data(self, receiver_data: dict[str, str]) -> None:
        for key, selectors in CheckoutSelectors.RECEIVER_INPUTS.items():
            if key not in receiver_data:
                continue
            self.fill_first_visible(selectors, receiver_data[key])

    def choose_pickup_details(self, location: str | None, point_name: str | None) -> None:
        if location:
            self.fill_first_visible(CheckoutSelectors.PICKUP_LOCATION_INPUTS, location)
            self.click_first_visible(CheckoutSelectors.PICKUP_SEARCH_BUTTONS, timeout=1500)
        if point_name:
            if self._select_pickup_point_by_name(point_name):
                return
        self.click_first_visible(CheckoutSelectors.PICKUP_POINT_OPTIONS, timeout=3000)

    def _select_pickup_point_by_name(self, point_name: str) -> bool:
        selector = CheckoutSelectors.PICKUP_POINT_TILE_BY_NAME.format(point_name=point_name)
        point = self.locator(selector)
        if point.count() > 0:
            for idx in range(min(point.count(), 3)):
                try:
                    point.nth(idx).click(timeout=2500)
                    return True
                except Exception:
                    continue

        scroll_container = self.locator(CheckoutSelectors.PICKUP_SCROLL_CONTAINER)
        if scroll_container.count() > 0:
            for step in range(1, 11):
                try:
                    scroll_container.first.evaluate(
                        "(el, ratio) => { el.scrollTop = el.scrollHeight * ratio; }",
                        step / 10,
                    )
                except Exception:
                    continue
                point = self.locator(selector)
                if point.count() == 0:
                    continue
                for idx in range(min(point.count(), 3)):
                    try:
                        point.nth(idx).click(timeout=2500)
                        return True
                    except Exception:
                        continue
        return False

    def select_lift_option_if_available(self, with_lift: bool) -> None:
        checkbox = self.locator(CheckoutSelectors.DELIVERY_WITH_LIFT_CHECKBOX)
        if checkbox.count() == 0:
            return
        try:
            if with_lift:
                checkbox.first.check(timeout=1000)
                self.click(CheckoutSelectors.DELIVERY_WITH_LIFT_TILE)
            else:
                checkbox.first.uncheck(timeout=1000)
        except Exception:
            return

    def select_payment(self, payment_label: str) -> None:
        self.click(CheckoutSelectors.PAYMENT_TILE_BY_TEXT.format(payment=payment_label))

    def accept_all_visible_terms(self) -> None:
        for selector in CheckoutSelectors.TERMS_CHECKBOX_IDS:
            try:
                self.locator(selector).first.check(timeout=1000)
            except Exception:
                continue

    def submit_order(self) -> bool:
        return self.click_first_visible(CheckoutSelectors.SUBMIT_ORDER_BUTTONS, timeout=5000)
