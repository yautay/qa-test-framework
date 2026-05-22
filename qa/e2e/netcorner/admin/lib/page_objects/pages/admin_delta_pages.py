from __future__ import annotations

import base64
import random
import re
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState
from qa.e2e.netcorner.admin.lib.timeouts import ELEMENT_VISIBLE_MS, HTTP_REQUEST_TIMEOUT_S, QUICK_PROBE_MS


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

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminCategorySearchKeywordsPage:
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

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminSettingsExceptionListPage:
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

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminSearchCodeGroupPage:
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

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminOrdersReportsPage:
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

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminMissingLinksPage:
        super().wait_loaded(state=state, timeout=timeout)
        expect(self.__header).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def has_link_entry(self, link_fragment: str) -> bool:
        row = self.page.locator("table tbody tr").filter(has_text=link_fragment).first
        return row.count() > 0 and row.is_visible(timeout=ELEMENT_VISIBLE_MS)


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
    _CB_CURRENCY_PLN = "#associated_promotion_price_currency_country_id_1"
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

    def get_limited_sale_settings(self) -> dict[str, int | str]:
        """Read active limited-sale settings from promotions tab edit form."""
        self._enter_promotions_tab()
        edit_active = self.page.locator(
            "#ui-tabs-1 tr:has(td:nth-child(3) img[alt='Tick']) a:has(img[alt='Edit_icon'])"
        ).first
        expect(edit_active).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        edit_active.click()
        self._wait_ajax()
        expect(self.page.locator(self._INPUT_DATE_TO)).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

        date_to = self.page.locator(self._INPUT_DATE_TO).input_value().strip()
        sold_amount = int((self.page.locator(self._INPUT_SOLD_AMOUNT).input_value() or "0").strip())
        total_amount = int((self.page.locator(self._INPUT_TOTAL_AMOUNT).input_value() or "0").strip())
        per_customer = int((self.page.locator(self._INPUT_PER_CUSTOMER).input_value() or "0").strip())

        return {
            "date_to": date_to,
            "sold_amount": sold_amount,
            "total_amount": total_amount,
            "per_customer": per_customer,
        }

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
            if not name_inp.is_visible(timeout=ELEMENT_VISIBLE_MS):
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
            if list_btn.is_visible(timeout=QUICK_PROBE_MS):
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
        for cb_sel in (self._CB_PL, self._CB_PL_MOBILE, self._CB_CURRENCY_PLN):
            cb_el = self.page.locator(cb_sel)
            if cb_el.count() and not cb_el.is_checked():
                cb_el.check(force=True)
        self.page.locator(self._BTN_SAVE).click()
        self._wait_ajax()


@dataclass(frozen=True)
class CartOfferData:
    """Data returned after creating a cart offer in admin."""
    offer_id: str


class AdminCartOfferPage(AdminBasePage):
    """Admin cart offer create/edit page.

    URL create: <admin_base_url>/admin.php/cartOfferAdmin/create/pl
    URL edit:   <admin_base_url>/admin.php/cartOfferAdmin/edit/pl/cart_offer_id/{id}

    Locators confirmed from Selenium CartOfferLocators.py + CartOfferObjects.py.
    """

    PAGE_ID = "netcorner.admin.cart_offer.form"
    CREATE_PATH = "/admin.php/cartOfferAdmin/create/pl"
    LIST_PATH = "/admin.php/cartOfferAdmin/list/pl"

    # Form selectors
    _SEL_CHANNEL = "#ktr_cart_offer_cart_offer_sales_channel_id"
    _SEL_ACTIVE = "#ktr_cart_offer_cart_offer_active"
    _SEL_PRICE_TYPE_FIXED = "#ktr_cart_offer_cart_offer_price_type_1"
    _SEL_PRICE_TYPE_DYNAMIC = "#ktr_cart_offer_cart_offer_price_type_2"
    _SEL_PRICE_CATEGORY = "#priceCategory"
    _INPUT_EXPIRATION = "#ktr_cart_offer_cart_offer_expires_at"
    _INPUT_EMAIL = "#ktr_cart_offer_cart_offer_customer_email"
    _INPUT_SUBJECT = "#ktr_cart_offer_cart_offer_email_subject"
    _BTN_SAVE = "input[name='save'][type='submit'], input[value='zapisz']"
    # Product row: product ID used in selector
    _INPUT_PRODUCT_PRICE_TMPL = "#cartOfferProducts_{product_id}_priceGross"
    _INPUT_PRODUCT_ROW_ID_TMPL = "#cartOfferProducts_{product_id}_id"
    _ROW_RECALC_LINK_TMPL = "#cartOfferProductRow_{product_id} a:has(img[alt='dodaj'])"
    _PRODUCT_ROW_SEL = "tr[id^='cartOfferProductRow_']"
    # Row with add-product button
    _BTN_SEND_EMAIL = "input[value='Wyślij e-mail']"
    _LINK_SEND_TO_CUSTOMER = "a[onclick*='cartOfferAdmin/sendToCustomer']"
    _INPUT_SEND_TO_CUSTOMER_MAIL = "#cart_offer_send_to_customer_mail"
    # Product section
    _INPUT_PRODUCT_SEARCH = "#addProductToOfferForm_searchField"
    _SELECT_PRODUCT_SEARCH_TYPE = "#addProductToOfferForm_searchType"
    _INPUT_PRODUCT_QTY = "#search_field"
    _LINK_ADD_PRODUCT = "a[onclick*='addProductToOffer']"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def navigate_to_create(self) -> AdminCartOfferPage:
        self.page.goto(f"{self.base_url}{self.CREATE_PATH}")
        return self.wait_loaded()

    def navigate_to_list(self) -> AdminCartOfferPage:
        self.page.goto(f"{self.base_url}{self.LIST_PATH}")
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminCartOfferPage:
        super().wait_loaded(state=state, timeout=timeout)
        form_timeout = timeout or self.DEFAULT_TIMEOUT
        expect(self.page.locator(self._SEL_CHANNEL)).to_be_visible(timeout=form_timeout)
        expect(self.page.locator(self._INPUT_PRODUCT_SEARCH)).to_be_visible(timeout=form_timeout)
        expect(self.page.locator(self._BTN_SAVE).first).to_be_visible(timeout=form_timeout)
        return self

    def _wait_product_row_loaded(self, *, timeout: int = 10_000) -> None:
        expect(self.page.locator(self._PRODUCT_ROW_SEL).first).to_be_visible(timeout=timeout)

    def _first_product_row_id(self) -> str:
        row_id_attr = self.page.locator(self._PRODUCT_ROW_SEL).first.get_attribute("id") or ""
        prefix = "cartOfferProductRow_"
        if not row_id_attr.startswith(prefix):
            raise RuntimeError(f"Unexpected cart offer product row id: '{row_id_attr}'")
        return row_id_attr.removeprefix(prefix)

    def create_cart_offer(
        self,
        *,
        product_id: int | str,
        qty: int = 1,
        recipient_email: str,
        channel_id: str = "1",
        price_type_id: str = "1",
        price_category_id: str | None = None,
        expiration_days: int = 7,
        fixed_price: str | None = None,
    ) -> str:
        """Fill and save the cart offer form. Returns the offer URL extracted from the list.

        Args:
            product_id: Product identifier entered in search field.
            qty: Quantity.
            recipient_email: Email to send the cart offer to.
            channel_id: Sales channel option value (default '1' = komputronik.pl).
            price_type_id: Price type select value. '1' = fixed, other = dynamic.
            price_category_id: Price category select value (optional).
            expiration_days: Days until offer expires.
            fixed_price: Fixed brutto price string (only for static/fixed price type).
        Returns:
            The cart offer URL taken from the success redirect URL or list.
        """
        expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime("%Y-%m-%d")

        self.wait_loaded()
        self.page.locator(self._SEL_CHANNEL).select_option(value=channel_id)

        # Active checkbox
        active_cb = self.page.locator(self._SEL_ACTIVE)
        if active_cb.count() and not active_cb.is_checked():
            active_cb.check()

        # Expiration date — datepicker, set via JS
        self.page.eval_on_selector(
            self._INPUT_EXPIRATION, f"el => el.value = '{expiration_date}'"
        )

        # Email recipient
        email_inp = self.page.locator(self._INPUT_EMAIL).first
        expect(email_inp).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        email_inp.fill(recipient_email)

        # Price type
        if price_type_id == "1":
            self.page.locator(self._SEL_PRICE_TYPE_FIXED).first.check()
        else:
            self.page.locator(self._SEL_PRICE_TYPE_DYNAMIC).first.check()

        # Price category
        if price_category_id is not None:
            price_cat_sel = self.page.locator(self._SEL_PRICE_CATEGORY)
            if price_cat_sel.count() > 0:
                price_cat_sel.first.select_option(value=price_category_id)

        # Add product via cartOfferAdmin AJAX product form
        self.page.locator(self._SELECT_PRODUCT_SEARCH_TYPE).first.select_option(value="ktr_product.PRODUCT_CODE_MAX")
        self.page.locator(self._INPUT_PRODUCT_SEARCH).first.fill(str(product_id))
        self.page.locator(self._INPUT_PRODUCT_QTY).first.fill(str(qty))
        self.page.locator(self._LINK_ADD_PRODUCT).first.click()
        self._wait_product_row_loaded()

        # Fixed price per product (only when price_type is fixed)
        if fixed_price is not None:
            row_product_id = self._first_product_row_id()
            price_input_sel = self._INPUT_PRODUCT_PRICE_TMPL.format(product_id=row_product_id)
            price_inp = self.page.locator(price_input_sel).first
            expect(price_inp).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
            price_inp.fill(fixed_price)
            price_inp.press("Enter")
            recalc = self.page.locator(self._ROW_RECALC_LINK_TMPL.format(product_id=row_product_id))
            if recalc.count() > 0:
                recalc.first.click()
            row_id_input = self.page.locator(self._INPUT_PRODUCT_ROW_ID_TMPL.format(product_id=row_product_id)).first
            if row_id_input.count() == 0:
                raise RuntimeError(f"Brak pola ID dla produktu oferty: {row_product_id}")

        self.page.locator(self._BTN_SAVE).first.click()
        self.page.wait_for_load_state("domcontentloaded")
        if self.page.locator(self._BTN_SEND_EMAIL).count() == 0:
            expect(self.page.locator(self._LINK_SEND_TO_CUSTOMER).first).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

        # Return current URL — it redirects to the edit page with id in path
        return self.page.url

    def send_offer_email(self) -> None:
        """Click 'Wyślij e-mail' to dispatch the cart offer email to the recipient."""
        legacy_btn = self.page.locator(self._BTN_SEND_EMAIL)
        if legacy_btn.count() > 0:
            btn = legacy_btn.first
            expect(btn).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
            btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            return

        send_link = self.page.locator(self._LINK_SEND_TO_CUSTOMER).first
        expect(send_link).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        send_mail = self.page.locator(self._INPUT_SEND_TO_CUSTOMER_MAIL).first
        if (send_mail.input_value() or "").strip() == "":
            customer_email = (self.page.locator(self._INPUT_EMAIL).first.input_value() or "").strip()
            if customer_email:
                send_mail.fill(customer_email)
        send_link.click()
        self.page.wait_for_timeout(QUICK_PROBE_MS)

    def get_offer_id_from_url(self) -> str | None:
        """Extract the offer id from the current admin URL (edit page)."""
        url = self.page.url
        match = re.search(r"/cartOfferAdmin/edit/pl/cart_offer_id/(\d+)", url)
        return match.group(1) if match else None


@dataclass(frozen=True)
class EmployeeProgramGroupData:
    """Data model for partner/employee group created in admin."""
    group_name: str
    price_category_id: str = "68"  # default employee price category
    enable_qr: bool = False
    phone_numbers: list[str] | None = None


class AdminEmployeeProgramPage(AdminBasePage):
    """Admin partner/employee group create/edit page.

    URL create: <admin_base_url>/admin.php/partnerEmployeeGroup/create/pl
    URL list:   <admin_base_url>/admin.php/partnerEmployeeGroup/list/pl
    URL edit:   <admin_base_url>/admin.php/partnerEmployeeGroup/edit/pl/id/{id}

    Locators confirmed from Selenium PartnerGroupLocators.py + PartnerGroupObjects.py.
    """

    PAGE_ID = "netcorner.admin.employee_program.form"
    CREATE_PATH = "/admin.php/partnerEmployeeGroup/create/pl"
    LIST_PATH = "/admin.php/partnerEmployeeGroup/list/pl"

    # Form selectors
    _INPUT_GROUP_NAME = "#ktr_partner_employee_group_group_name"
    _SELECT_PRICE_CATEGORY = "#ktr_partner_employee_group_group_price_category_id"
    _CB_ENABLE_QR = "#ktr_partner_employee_group_qr_code"
    _INPUT_SMS_MSG = "#ktr_partner_employee_group_group_sms_text"
    _INPUT_IMPORT_PHONES = "#ktr_partner_employee_group_phone_numbers_import"
    _BTN_SHOW_HASHES = "a[title*='Pokaż numery telefonów']"
    _ELEMENTS_HASHES = "tbody tr td:nth-child(4)"
    _BTN_GENERATE_QR = "a[title='Generuj nowy kod QR ']"
    _LINK_QR_DOWNLOAD = "a[title*='Pobierz kod QR']"
    _IMG_QR_CODE = "img[alt='QR Code']"
    _BTN_UNLINK_PHONES = "a[title*='Usuń numery telefonów']"
    _BTN_SAVE = "input[name='save'][type='submit']"
    # Delete button in list
    _BTN_DELETE_IN_LIST = "a[href*='partnerEmployeeGroup/delete']"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def navigate_to_create(self) -> AdminEmployeeProgramPage:
        self.page.goto(f"{self.base_url}{self.CREATE_PATH}")
        return self.wait_loaded()

    def navigate_to_list(self) -> AdminEmployeeProgramPage:
        self.page.goto(f"{self.base_url}{self.LIST_PATH}")
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def navigate_to_edit(self, group_id: str) -> AdminEmployeeProgramPage:
        self.page.goto(f"{self.base_url}/admin.php/partnerEmployeeGroup/edit/pl/group_id/{group_id}")
        return self.wait_loaded()

    def wait_loaded(
        self, *, state: LoadState = "domcontentloaded", timeout: int | None = None
    ) -> AdminEmployeeProgramPage:
        super().wait_loaded(state=state, timeout=timeout)
        from playwright.sync_api import expect as pw_expect
        pw_expect(self.page.locator(self._INPUT_GROUP_NAME)).to_be_visible(
            timeout=timeout or self.DEFAULT_TIMEOUT
        )
        return self

    def create_group(self, data: EmployeeProgramGroupData) -> str:
        """Fill and save the employee group form.

        Returns:
            The group ID extracted from the redirect URL after save.
        """
        self.page.locator(self._INPUT_GROUP_NAME).fill(data.group_name)

        price_cat_sel = self.page.locator(self._SELECT_PRICE_CATEGORY)
        if price_cat_sel.count():
            price_cat_sel.select_option(value=data.price_category_id)

        if data.enable_qr:
            qr_cb = self.page.locator(self._CB_ENABLE_QR)
            if qr_cb.count() and not qr_cb.is_checked():
                qr_cb.check()
        else:
            sms_message = self.page.locator(self._INPUT_SMS_MSG)
            if sms_message.count() > 0:
                sms_message.first.fill("Link do zalogowania:")

        phone_numbers = data.phone_numbers
        if phone_numbers is None and not data.enable_qr:
            phone_numbers = [f"{random.choice((50, 51, 53, 57, 60, 66, 69, 72, 73, 78, 79, 88))}{random.randint(0, 9_999_999):07d}" for _ in range(10)]

        if phone_numbers:
            phone_inp = self.page.locator(self._INPUT_IMPORT_PHONES)
            if phone_inp.count():
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as fp:
                    fp.write("\n".join(phone_numbers))
                    temp_path = fp.name
                phone_inp.set_input_files(temp_path)

        self.page.locator(self._BTN_SAVE).first.click(force=True)
        self.page.wait_for_load_state("domcontentloaded")

        group_id = self.get_group_id_from_url()
        if group_id:
            return group_id

        group_id_from_field = (self.page.locator("#ktr_partner_employee_group_id").first.input_value() or "").strip()
        if group_id_from_field.isdigit():
            return group_id_from_field

        return ""

    def get_group_id_from_url(self) -> str | None:
        """Extract the group id from the current admin URL."""
        url = self.page.url
        for pattern in (r"/partnerEmployeeGroup/edit/pl/group_id/(\d+)", r"/partnerEmployeeGroup/edit/pl/id/(\d+)"):
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_sms_hashes(self) -> list[str]:
        """Click 'Pokaż hashe' and return the list of SMS hash codes."""
        btn = self.page.locator(self._BTN_SHOW_HASHES)
        if btn.count() == 0:
            return []
        btn.first.click()
        self.page.wait_for_timeout(QUICK_PROBE_MS)
        hashes_el = self.page.locator(self._ELEMENTS_HASHES)
        return [
            hashes_el.nth(i).inner_text().strip()
            for i in range(hashes_el.count())
            if hashes_el.nth(i).inner_text().strip()
        ]

    def get_qr_code_value(self) -> str:
        """Return decoded QR payload URL when possible, otherwise raw QR source."""
        qr_img = self.page.locator(self._IMG_QR_CODE).first
        if qr_img.count() > 0:
            src = (qr_img.get_attribute("src") or "").strip()
            if src.startswith("data:image"):
                decoded = self._decode_qr_from_data_uri(src)
                if decoded:
                    return decoded
            if src:
                return src

        download_link = self.page.locator(self._LINK_QR_DOWNLOAD).first
        if download_link.count() > 0:
            href = (download_link.get_attribute("href") or "").strip()
            if href:
                resolved = href if href.startswith("http") else f"{self.base_url}{href}"
                decoded = self._decode_qr_from_image_url(resolved)
                if decoded:
                    return decoded
                return resolved
        return ""

    @staticmethod
    def _decode_qr_payload(raw_image: bytes) -> str | None:
        try:
            import cv2  # type: ignore[import-not-found]
            import numpy as np  # type: ignore[import-not-found]
        except ImportError:
            return None

        matrix = np.frombuffer(raw_image, np.uint8)
        img = cv2.imdecode(matrix, cv2.IMREAD_COLOR)
        if img is None:
            return None

        detector = cv2.QRCodeDetector()

        payload, _, _ = detector.detectAndDecode(img)
        payload_text = str(payload or "").strip()
        if payload_text:
            return payload_text

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_with_border = cv2.copyMakeBorder(
            gray,
            40,
            40,
            40,
            40,
            cv2.BORDER_CONSTANT,
            value=255,
        )

        payload, _, _ = detector.detectAndDecode(gray_with_border)
        payload_text = str(payload or "").strip()
        if payload_text:
            return payload_text

        _, bw = cv2.threshold(gray_with_border, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        enlarged = cv2.resize(bw, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        payload, _, _ = detector.detectAndDecode(enlarged)
        payload_text = str(payload or "").strip()
        if payload_text:
            return payload_text

        detected, decoded_info, _, _ = detector.detectAndDecodeMulti(enlarged)
        if detected and decoded_info:
            for item in decoded_info:
                item_text = str(item or "").strip()
                if item_text:
                    return item_text

        return None

    def _decode_qr_from_data_uri(self, src: str) -> str | None:
        if "," not in src:
            return None
        _, encoded = src.split(",", 1)
        try:
            raw_image = base64.b64decode(encoded)
        except Exception:
            return None
        return self._decode_qr_payload(raw_image)

    def _decode_qr_from_image_url(self, url: str) -> str | None:
        try:
            with urllib.request.urlopen(url, timeout=HTTP_REQUEST_TIMEOUT_S) as response:
                raw_image = response.read()
        except Exception:
            return None
        return self._decode_qr_payload(raw_image)

    def generate_new_qr_code(self) -> None:
        """Click 'Generuj nowy kod QR' and wait for it."""
        btn = self.page.locator(self._BTN_GENERATE_QR)
        if btn.count() == 0:
            raise AssertionError("Nie znaleziono przycisku 'Generuj nowy kod QR'.")
        self.page.once("dialog", lambda dialog: dialog.accept())
        btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")

    def delete_group(self, group_id: str) -> None:
        """Navigate to list and delete the group with the given ID."""
        self.navigate_to_edit(group_id)

        unlink_button = self.page.locator(self._BTN_UNLINK_PHONES).first
        if unlink_button.count() > 0 and unlink_button.is_visible(timeout=QUICK_PROBE_MS):
            self.page.once("dialog", lambda dialog: dialog.accept())
            unlink_button.click()
            self.page.wait_for_load_state("domcontentloaded")

        delete_button = self.page.locator("input.sf_admin_action_delete, input[value='usuń']").first
        if delete_button.count() == 0:
            raise AssertionError(f"Nie znaleziono przycisku usuwania dla grupy id={group_id}.")
        self.page.once("dialog", lambda dialog: dialog.accept())
        delete_button.click()
        self.page.wait_for_load_state("domcontentloaded")

    def is_group_registered(self, email: str) -> bool:
        """Check if a user email appears in the group member list on the edit page."""
        return self.page.locator(f"td:has-text('{email}')").count() > 0


__all__ = [
    "AdminCartOfferPage",
    "AdminCategorySearchKeywordsPage",
    "AdminEmployeeProgramPage",
    "AdminMissingLinksPage",
    "AdminOrdersReportsPage",
    "AdminProductOzoPage",
    "AdminSearchCodeGroupPage",
    "AdminSettingsExceptionListPage",
    "CartOfferData",
    "EmployeeProgramGroupData",
    "ListingExceptionEntry",
    "SearchKeywordEntry",
]
