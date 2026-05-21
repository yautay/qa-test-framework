from __future__ import annotations

from urllib.parse import quote_plus

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState
from qa.e2e.netcorner.admin.lib.timeouts import QUICK_PROBE_MS


class AdminPromoCodePage(AdminBasePage):
    PAGE_ID = "netcorner.admin.promo_code.list"
    PATH = "/admin.php/codePromotionService/list/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__create_button = page.locator("input.sf_admin_action_create").first
        self.__code_rows = page.locator("table tbody tr")
        self.__type_select = page.locator("#ktr_code_promotion_code_promotion_type")
        self.__code_input = page.locator("#ktr_code_promotion_code_promotion_code")
        self.__active_checkbox = page.locator("#ktr_code_promotion_code_promotion_active")
        self.__multiple_checkbox = page.locator("#ktr_code_promotion_code_promotion_is_multiple")
        self.__promotion_search_input = page.locator(".vue-treeselect__input").first
        self.__save_button = page.locator("input[name='save'][type='submit'], input.sf_admin_action_save").first
        self.__list_button = page.locator("input.sf_admin_action_list").first
        self.__duplicate_warning = page.locator(".form-errors dd").filter(
            has_text="Podany kod jest już przypisany do innego kodu promocyjnego"
        ).first

    def navigate_to(self) -> AdminPromoCodePage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminPromoCodePage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__create_button).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def has_code(self, code: str) -> bool:
        encoded = quote_plus(f"{code}*")
        self.page.goto(f"{self.base_url}{self.PATH}?filters[code_promotion_code]={encoded}&filter=filtruj")
        self.page.wait_for_load_state("domcontentloaded")
        return self.__code_rows.filter(has_text=code).count() > 0

    def ensure_promo_code(self, *, code: str, promotion_name: str, type_label: str = "Promocja") -> None:
        self.navigate_to()
        if self.has_code(code):
            return

        self.__create_button.click()
        expect(self.__type_select).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

        self.__type_select.select_option(label=type_label)
        self.__code_input.fill(code)

        if not self.__active_checkbox.is_checked():
            self.__active_checkbox.check()
        if not self.__multiple_checkbox.is_checked():
            self.__multiple_checkbox.check()

        self.__promotion_search_input.click()
        self.__promotion_search_input.fill(promotion_name)
        promotion_option = self.page.locator(".vue-treeselect__menu label").filter(has_text=promotion_name).first
        if promotion_option.count() == 0:
            available = [
                text.strip()
                for text in self.page.locator(".vue-treeselect__menu label").all_inner_texts()
                if text.strip()
            ]
            raise AssertionError(
                f"Nie znaleziono promocji '{promotion_name}' potrzebnej do utworzenia kodu '{code}'. "
                f"Dostępne opcje: {available[:5]}"
            )
        promotion_option.click()

        self.__save_button.click()
        self.page.wait_for_load_state("domcontentloaded")

        if self.__duplicate_warning.count() > 0 and self.__duplicate_warning.is_visible(timeout=QUICK_PROBE_MS):
            if self.__list_button.is_visible(timeout=QUICK_PROBE_MS):
                self.__list_button.click()
                self.page.wait_for_load_state("domcontentloaded")

        assert self.has_code(code), f"Nie udało się utworzyć kodu promocyjnego '{code}'."

    def create_aggregator_code(self, *, code: str, promotion_name: str) -> None:
        self.ensure_promo_code(code=code, promotion_name=promotion_name, type_label="Promocja")
