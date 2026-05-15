from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState


@dataclass(frozen=True)
class SearchKeywordEntry:
    category_id: str
    category_name: str
    phrases: list[str]


@dataclass(frozen=True)
class ListingExceptionEntry:
    category_id: str
    config_name: str


class AdminCategorySearchKeywordsPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.category_search_keywords.list"
    PATH = "/admin.php/categorySearchKeyword/list/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__header = page.locator("h1").filter(has_text="Kategorie - Frazy wyszukiwania").first
        self.__rows = page.locator("table tbody tr")

    def navigate_to(self) -> AdminCategorySearchKeywordsPage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminCategorySearchKeywordsPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__header).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        expect(self.__rows.first).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def get_entries(self, *, limit: int = 5) -> list[SearchKeywordEntry]:
        entries: list[SearchKeywordEntry] = []
        for row_index in range(min(self.__rows.count(), limit)):
            cells = self.__rows.nth(row_index).locator("td")
            category_cell = (cells.nth(0).inner_text() or "").strip()
            phrases_cell = (cells.nth(1).inner_text() or "").strip()
            if not category_cell or not phrases_cell or "(" not in category_cell:
                continue
            category_name, category_id = category_cell.rsplit("(", 1)
            phrases = [phrase.strip() for phrase in phrases_cell.split(",") if phrase.strip()]
            entries.append(
                SearchKeywordEntry(
                    category_id=category_id.rstrip(")"),
                    category_name=category_name.strip(),
                    phrases=phrases,
                )
            )
        return entries


class AdminSettingsExceptionListPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.settings_exception.list"
    PATH = "/admin.php/settingsExceptionList/list/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__header = page.locator("h1").filter(has_text="Wyjątki konfiguracji").first
        self.__rows = page.locator("table tbody tr")

    def navigate_to(self) -> AdminSettingsExceptionListPage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminSettingsExceptionListPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__header).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        expect(self.__rows.first).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def get_category_entries(self, *, limit: int = 5) -> list[ListingExceptionEntry]:
        entries: list[ListingExceptionEntry] = []
        for row_index in range(min(self.__rows.count(), limit)):
            row = self.__rows.nth(row_index)
            cells = row.locator("td")
            config_type = (cells.nth(0).inner_text() or "").strip()
            category_id = (cells.nth(1).inner_text() or "").strip()
            config_name = (cells.nth(2).inner_text() or "").strip()
            if config_type != "Kategoria" or not category_id or not config_name:
                continue
            entries.append(ListingExceptionEntry(category_id=category_id, config_name=config_name))
        return entries


class AdminSearchCodeGroupPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.search_code_group.form"
    CREATE_PATH = "/admin.php/searchCodeGroup/create/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__code = page.locator("#code_group_code")
        self.__sales_channel = page.locator("#code_group_sales_channel_id")
        self.__max_codes = page.locator("#code_group_max_codes")
        self.__save = page.locator("input[name='save'][type='submit']").first

    def navigate_to_create(self) -> AdminSearchCodeGroupPage:
        self.page.goto(f"{self.base_url}{self.CREATE_PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminSearchCodeGroupPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__code).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        expect(self.__max_codes).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def create_group(self, *, code: str, max_codes: list[str], sales_channel_id: str = "1") -> None:
        self.__code.fill(code)
        self.__sales_channel.select_option(value=sales_channel_id)
        self.__max_codes.fill(", ".join(max_codes))
        self.__save.click()
        self.page.wait_for_load_state("domcontentloaded")


class AdminOrdersReportsPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.orders.list"
    PATH = "/admin.php/orders/list/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__header = page.locator("h1").filter(has_text="Lista zamówień").first
        self.__rows = page.locator("table tbody tr")

    def navigate_to(self) -> AdminOrdersReportsPage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminOrdersReportsPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__header).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        expect(self.__rows.first).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def get_recent_order_numbers(self, *, limit: int = 5) -> list[str]:
        order_numbers: list[str] = []
        for row_index in range(min(self.__rows.count(), limit)):
            cells = self.__rows.nth(row_index).locator("td")
            order_number = (cells.nth(1).inner_text() or "").strip()
            if order_number:
                order_numbers.append(order_number)
        return order_numbers

    def get_report_action_texts(self) -> list[str]:
        tokens = [
            "Pobierz zamówienia w pliku CSV (jeden produkt w jednej linii)",
            "Pobierz zamówienia w pliku CSV (jedno zamówienie w jednej linii)",
            "Eksport zamówień do systemu Call Center",
            "Raport wartości zamówień",
        ]
        return [token for token in tokens if self.page.get_by_text(token, exact=True).count() > 0]


class AdminMissingLinksPage(AdminBasePage):
    PAGE_ID = "netcorner.admin.missing_links.list"
    PATH = "/admin.php/missingLink/list/pl"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.__header = page.locator("h1").filter(has_text="Rejestr URL 404 - lista").first

    def navigate_to(self) -> AdminMissingLinksPage:
        self.page.goto(f"{self.base_url}{self.PATH}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminMissingLinksPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__header).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def has_link_entry(self, link_fragment: str) -> bool:
        row = self.page.locator("table tbody tr").filter(has_text=link_fragment).first
        return row.count() > 0 and row.is_visible(timeout=5_000)


# ---------------------------------------------------------------------------
# OZO / Limited-sale reset — product promotions tab
# ---------------------------------------------------------------------------

class AdminProductOzoPage(AdminBasePage):
    """Admin product edit page — promotions tab.

    Used to reset OZO (limited-sale) counters before/after test runs so that
    the environment is in a deterministic state.

    The promotions tab uses jQuery UI tabs with AJAX lazy-loading.
    All interactions inside the tab are AJAX in-place (content replaces
    ``#sf_fieldset_product_promotion``), NOT full page navigations.
    """

    PAGE_ID = "netcorner.admin.product_ozo.edit"

    # Promotions tab anchor (jQuery UI tabs — CSS selector)
    _TAB_PROMOTIONS = "a[href='#ui-tabs-1']"
    # AJAX-loaded container inside the promotions tab
    _PROMOTIONS_CONTAINER = "#ui-tabs-1 #sf_fieldset_product_promotion"
    # Row with Edit button (any row that has an Edit_icon link)
    _EDIT_BTN_IN_ROW = "#ui-tabs-1 a:has(img[alt='Edit_icon'])"
    # "stwórz promocje" button (AJAX, not submit)
    _BTN_NEW = "#ui-tabs-1 input.sf_admin_action_create"
    # "lista promocji" button inside promotion form
    _BTN_LIST = "#ui-tabs-1 input[value='lista promocji']"
    # Promotion form fields (appear inside container after AJAX create/edit)
    _INPUT_NAME = "#ktr_promotion_promotion_name"
    _INPUT_ACTIVATED = "#ktr_promotion_promotion_active"
    _INPUT_ACTIVATED_SEZAM = "#ktr_promotion_promotion_active_in_sezam"
    _INPUT_DATE_FROM = "#ktr_promotion_promotion_date_from"
    _INPUT_DATE_TO = "#ktr_promotion_promotion_date_to"
    _INPUT_SOLD_AMOUNT = "#ktr_promotion_promotion_limited_sale_sold_amount"
    _INPUT_TOTAL_AMOUNT = "#ktr_promotion_promotion_limited_sale_amount"
    _INPUT_PER_CUSTOMER = "#ktr_promotion_promotion_limited_sale_can_sale_for_one_customer"
    _SELECT_TYPE = "#ktr_promotion_promotion_promotion_type_id"
    _INPUT_VALUE = "#ktr_promotion_promotion_value"
    _CB_PL = "#associated_promotion_price_category_10"
    _CB_PL_MOBILE = "#associated_promotion_price_category_71"
    _BTN_SAVE = "#ui-tabs-1 input[name='submit_promotion']"

    def __init__(self, page: Page, base_url: str, product_id: int) -> None:
        super().__init__(page, base_url)
        self._product_id = product_id
        self._path = f"/admin.php/product/edit/pl/product_id/{product_id}"

    def navigate_to(self) -> AdminProductOzoPage:
        self.page.goto(f"{self.base_url}{self._path}")
        return self.wait_loaded()

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminProductOzoPage:
        super().wait_loaded(state=state, timeout=timeout)
        # jQuery UI tabs render after DOM — wait for the Promocje tab anchor
        expect(self.page.locator(self._TAB_PROMOTIONS)).to_be_visible(
            timeout=timeout or self.DEFAULT_TIMEOUT
        )
        return self

    def reset_ozo_promotion(
        self,
        *,
        sold_amount: int = 3,
        total_amount: int = 50,
        per_customer: int = 5,
        price_type_value: str = "3",
        promotion_value: float = 1,
    ) -> None:
        """Deactivate all active promotions and create a fresh OZO promotion.

        Mirrors the Selenium ``AdminFunctionalObjects.reset_ozo_sales()`` flow.
        All interactions are AJAX in-place inside ``#sf_fieldset_product_promotion``.
        """
        self._enter_promotions_tab()
        self._deactivate_all_active_promotions()
        self._create_ozo_promotion(
            sold_amount=sold_amount,
            total_amount=total_amount,
            per_customer=per_customer,
            price_type_value=price_type_value,
            promotion_value=promotion_value,
        )

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _enter_promotions_tab(self) -> None:
        """Click the Promocje tab and wait for AJAX content (table) to load."""
        tab = self.page.locator(self._TAB_PROMOTIONS)
        expect(tab).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        tab.click()
        # Tab content is AJAX-loaded — wait for the promotions table to appear
        expect(self.page.locator("#ui-tabs-1 table")).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

    def _wait_ajax(self) -> None:
        """Wait for AJAX indicator to disappear (admin uses Element.show/hide('indicator'))."""
        indicator = self.page.locator("#indicator")
        if indicator.count():
            indicator.wait_for(state="hidden", timeout=self.DEFAULT_TIMEOUT)

    def _deactivate_all_active_promotions(self) -> None:
        """Deactivate every active promotion in the list.

        Iterates until no active promotions remain.  The safety cap is set
        high enough to cover even heavily polluted test environments.
        """
        for _ in range(50):  # safety cap — covers up to 50 active promotions
            # Re-query active rows on each iteration (list refreshes after each save)
            active_edit_btns = self.page.locator(
                "#ui-tabs-1 tr:has(td:nth-child(3) img[alt='Tick']) a:has(img[alt='Edit_icon'])"
            )
            if active_edit_btns.count() == 0:
                break
            active_edit_btns.first.click()
            self._wait_ajax()
            # Wait for form to appear
            name_inp = self.page.locator(self._INPUT_NAME)
            if not name_inp.is_visible(timeout=5_000):
                break
            # Uncheck both active flags
            activated = self.page.locator(self._INPUT_ACTIVATED)
            if activated.count():
                if activated.is_checked():
                    activated.uncheck()
                sezam = self.page.locator(self._INPUT_ACTIVATED_SEZAM)
                if sezam.count() and sezam.is_checked():
                    sezam.uncheck()
                self.page.locator(self._BTN_SAVE).click()
                self._wait_ajax()
            # Back to list — wait for table to re-appear
            list_btn = self.page.locator(self._BTN_LIST)
            if list_btn.is_visible(timeout=3_000):
                list_btn.click()
                self._wait_ajax()
                expect(self.page.locator("#ui-tabs-1 table")).to_be_visible(
                    timeout=self.DEFAULT_TIMEOUT
                )
            else:
                break

    def _create_ozo_promotion(
        self,
        *,
        sold_amount: int,
        total_amount: int,
        per_customer: int,
        price_type_value: str,
        promotion_value: float,
    ) -> None:
        """Click 'stwórz promocje', fill the form, save."""
        now = datetime.now()
        name = f"OzO Limited Sale Promotion {now.strftime('%Y%m%d%H%M%S')}"
        date_from = now.strftime("%Y-%m-%d %H:%M")
        date_to = (now + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")

        btn_new = self.page.locator(self._BTN_NEW)
        expect(btn_new).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        btn_new.click()
        self._wait_ajax()

        # Wait for form fields to appear inside the container
        expect(self.page.locator(self._INPUT_NAME)).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

        # Fill via JS for text/number inputs; use check() for checkboxes
        self.page.locator(self._INPUT_NAME).fill(name)
        # active + active_in_sezam are checkboxes
        for cb_sel in (self._INPUT_ACTIVATED, self._INPUT_ACTIVATED_SEZAM):
            cb = self.page.locator(cb_sel)
            if cb.count() and not cb.is_checked():
                cb.check()
        self.page.locator(self._SELECT_TYPE).select_option(value=price_type_value)
        self.page.locator(self._INPUT_VALUE).fill(str(promotion_value))
        # date fields are readonly datepickers — set via JS
        self.page.eval_on_selector(self._INPUT_DATE_FROM, f"el => el.value = '{date_from}'")
        self.page.eval_on_selector(self._INPUT_DATE_TO, f"el => el.value = '{date_to}'")
        self.page.locator(self._INPUT_SOLD_AMOUNT).fill(str(sold_amount))
        self.page.locator(self._INPUT_TOTAL_AMOUNT).fill(str(total_amount))
        self.page.locator(self._INPUT_PER_CUSTOMER).fill(str(per_customer))
        # Price categories (may be off-screen — force=True)
        for cb_sel in (self._CB_PL, self._CB_PL_MOBILE):
            cb_el = self.page.locator(cb_sel)
            if cb_el.count() and not cb_el.is_checked():
                cb_el.check(force=True)
        self.page.locator(self._BTN_SAVE).click()
        self._wait_ajax()


__all__ = [
    "AdminCategorySearchKeywordsPage",
    "AdminMissingLinksPage",
    "AdminOrdersReportsPage",
    "AdminProductOzoPage",
    "AdminSearchCodeGroupPage",
    "AdminSettingsExceptionListPage",
    "ListingExceptionEntry",
    "SearchKeywordEntry",
]
