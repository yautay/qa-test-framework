from __future__ import annotations

from dataclasses import dataclass

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


__all__ = [
    "AdminCategorySearchKeywordsPage",
    "AdminMissingLinksPage",
    "AdminOrdersReportsPage",
    "AdminSearchCodeGroupPage",
    "AdminSettingsExceptionListPage",
    "ListingExceptionEntry",
    "SearchKeywordEntry",
]
