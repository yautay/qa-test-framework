from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState


class AdminAggregatorCreatePage(AdminBasePage):
    PAGE_ID = "netcorner.admin.aggregator.create"
    PATH = "/admin.php/promotionAggregator/create/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__name = page.locator("#ktr_promotion_aggregator_name")
        self.__work_name = page.locator("#ktr_promotion_aggregator_aggregator_work_name")
        self.__url = page.locator("#ktr_promotion_aggregator_url")
        self.__published = page.locator("#ktr_promotion_aggregator_active")
        self.__sales_channel_pl = page.locator("#ktr_promotion_aggregator_promotion_aggregator_sales_channels_1")
        self.__save = page.locator("input.sf_admin_action_save").first

    def navigate_to(self) -> AdminAggregatorCreatePage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminAggregatorCreatePage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__name).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def create(self, *, name: str, work_name: str, url_slug: str, published: bool = True) -> int:
        self.__name.fill(name)
        self.__work_name.fill(work_name)
        self.__url.fill(url_slug)
        if self.__sales_channel_pl.count() and not self.__sales_channel_pl.is_checked():
            self.__sales_channel_pl.check()
        if self.__published.count() and self.__published.is_checked() != published:
            self.__published.click()
        self.__save.click()
        self.page.wait_for_load_state("domcontentloaded")
        match = re.search(r"/id/(\d+)", self.page.url)
        if not match:
            raise RuntimeError(f"Nie udało się odczytać ID agregatora po zapisie: {self.page.url}")
        return int(match.group(1))


class AdminAggregatorEditPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.aggregator.edit"

    def __init__(self, page: Page, base_url: str, aggregator_id: int) -> None:
        super().__init__(page, base_url)
        self.__aggregator_id = aggregator_id
        self.__add_element = page.locator("input.sf_admin_action_create[value='Dodaj nowy element']").first

    @property
    def path(self) -> str:
        return f"/admin.php/promotionAggregator/edit/pl/id/{self.__aggregator_id}"

    def navigate_to(self) -> AdminAggregatorEditPage:
        self.page.goto(f"{self.base_url}{self.path}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminAggregatorEditPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__add_element).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def open_add_element(self) -> None:
        self.__add_element.click()
        self.page.wait_for_load_state("domcontentloaded")


class AdminAggregatorItemCreatePage(AdminBasePage):
    PAGE_ID = "netcorner.admin.aggregator.item.create"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__name = page.locator("#ktr_promotion_aggregator_item_name")
        self.__section_code = page.locator("#ktr_promotion_aggregator_item_item_section_code")
        self.__products_source_code = page.locator("#ktr_promotion_aggregator_item_product_source_CODE")
        self.__product_codes = page.locator("#ktr_promotion_aggregator_item_product_codes")
        self.__discount_code = page.locator("#ktr_promotion_aggregator_item_product_discount_code").first
        self.__save = page.locator("input.sf_admin_action_save").first

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminAggregatorItemCreatePage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__name).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def create_products_item(
        self,
        *,
        name: str,
        section_code: str,
        product_codes: str,
        discount_code: str | None = None,
    ) -> None:
        self.__name.fill(name)
        self.__section_code.fill(section_code)
        self.__products_source_code.check()
        self.__product_codes.fill(product_codes)
        if discount_code:
            self.__discount_code.fill(discount_code)
        self.__save.click()
        self.page.wait_for_load_state("domcontentloaded")


__all__ = [
    "AdminAggregatorCreatePage",
    "AdminAggregatorEditPage",
    "AdminAggregatorItemCreatePage",
]
