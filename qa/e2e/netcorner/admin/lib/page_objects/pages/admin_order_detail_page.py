from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from playwright.sync_api import Page

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState
from qa.e2e.netcorner.admin.lib.test_data.admin_order_models import AdminOrderData, AdminOrderProduct


def _parse_price(raw: str) -> Decimal:
    """Convert Polish-formatted price string (e.g. '1 234,56 zł') to Decimal."""
    cleaned = re.sub(r"[^\d,.]", "", raw.replace(",", "."))
    # If there are multiple dots, only the last is decimal separator
    parts = cleaned.rsplit(".", 1)
    normalized = parts[0].replace(".", "") + ("." + parts[1] if len(parts) == 2 else "")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return Decimal("0.00")


class AdminOrderDetailPage(AdminBasePage):
    """Admin order detail / edit page.

    URL: <admin_base_url>/admin.php/orders/edit/pl/order_id/{id}
    Confirmed live against komputronik-galak env (2026-05-14).

    Key locators (all confirmed from live HTML):

        Container:
            #sf_admin_container  h1:has-text('Edycja zamówienia')

        Orderer / purchaser / receiver blocks:
            #order_orderer_data
            #order_purchaser_data
            #order_receiver_data

        Status (clickable link that opens a dropdown via AJAX):
            #orderStatus > a

        Prices:
            #productBruttoSum        — gross total
            #edit_price_shipping     — shipping price
            #edit_price_shipping_parameter — shipping surcharge

        Parameter card:
            a[href*='order_parameter_card_id']

        Order comment:
            .form-row:has-text('komentarz')

        NIP in purchaser block:
            #order_purchaser_data:has-text('NIP')
    """

    PAGE_ID = "netcorner.admin.orders.detail"

    _LOC_PAGE_HEADER = "h1:has-text('Edycja zamówienia')"
    _LOC_ADMIN_CONTAINER = "#sf_admin_container"

    _LOC_ORDERER_DATA = "#order_orderer_data"
    _LOC_PURCHASER_DATA = "#order_purchaser_data"
    _LOC_RECEIVER_DATA = "#order_receiver_data"

    # Status — shown as a clickable <a> inside #orderStatus
    _LOC_ORDER_STATUS = "#orderStatus > a"

    _LOC_SUMMARY_PRICE = "#productBruttoSum"
    _LOC_SHIPPING_PRICE = "#edit_price_shipping"
    _LOC_SHIPPING_PRICE_PARAM = "#edit_price_shipping_parameter"

    _LOC_PARAMETER_CARD = "a[href*='order_parameter_card_id']"
    _LOC_ORDER_COMMENT = ".form-row:has-text('komentarz')"

    # Status change: clicking #orderStatus > a triggers an AJAX call that replaces
    # the content of #orderStatus with a <select name containing 'status_id'>
    _LOC_STATUS_SELECT = "select[id*='status_id']"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminOrderDetailPage:
        super().wait_loaded(state=state, timeout=timeout)
        self.page.locator(self._LOC_PAGE_HEADER).wait_for(state="visible", timeout=10_000)
        return self

    # ------------------------------------------------------------------
    # Data reading
    # ------------------------------------------------------------------

    def get_order_number(self) -> str:
        """Return the order number from the page header text (e.g. '181255/2026')."""
        header_text = self.page.locator(self._LOC_PAGE_HEADER).inner_text(timeout=5_000)
        # Header: "Edycja zamówienia" — order number is displayed in the fieldset header below
        # Fall back to reading from page title or URL
        match = re.search(r"\d+/\d{4}", header_text)
        if match:
            return match.group(0)
        # Try the content header section
        content_header = self.page.locator("#sf_admin_header").inner_text(timeout=3_000)
        match = re.search(r"\d+/\d{4}", content_header)
        return match.group(0) if match else ""

    def get_status(self) -> str:
        """Return current order status text."""
        return self.page.locator(self._LOC_ORDER_STATUS).inner_text(timeout=5_000).strip()

    def get_summary_price_gross(self) -> Decimal:
        raw = self.page.locator(self._LOC_SUMMARY_PRICE).inner_text(timeout=5_000)
        return _parse_price(raw)

    def get_shipping_price(self) -> Decimal:
        raw_shipping = self.page.locator(self._LOC_SHIPPING_PRICE).inner_text(timeout=5_000)
        raw_param = self.page.locator(self._LOC_SHIPPING_PRICE_PARAM).inner_text(timeout=3_000)
        return _parse_price(raw_shipping) + _parse_price(raw_param)

    def get_purchaser_raw_lines(self) -> list[str]:
        """Return purchaser block text split into non-empty lines."""
        text = self.page.locator(self._LOC_PURCHASER_DATA).inner_text(timeout=5_000)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def get_receiver_raw_lines(self) -> list[str]:
        """Return receiver block text split into non-empty lines."""
        text = self.page.locator(self._LOC_RECEIVER_DATA).inner_text(timeout=5_000)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def get_nip(self) -> str:
        """Extract NIP value from the purchaser block (format 'NIP : XXXXXXXXXX')."""
        purchaser_text = self.page.locator(self._LOC_PURCHASER_DATA).inner_text(timeout=5_000)
        match = re.search(r"NIP\s*[:\-]\s*(\d[\d\s\-]+)", purchaser_text)
        return re.sub(r"[\s\-]", "", match.group(1)) if match else ""

    def get_parameter_card(self) -> str:
        loc = self.page.locator(self._LOC_PARAMETER_CARD)
        if loc.count() > 0:
            return loc.first.inner_text(timeout=3_000).strip()
        return ""

    def get_order_comment(self) -> str:
        loc = self.page.locator(self._LOC_ORDER_COMMENT)
        if loc.count() > 0:
            return loc.inner_text(timeout=3_000).strip()
        return ""

    def get_all_data(self, order_number: str = "") -> AdminOrderData:
        """Collect all readable order data into an AdminOrderData instance."""
        return AdminOrderData(
            order_number=order_number or self.get_order_number(),
            status=self.get_status(),
            summary_price_gross=self.get_summary_price_gross(),
            shipping_price=self.get_shipping_price(),
            purchaser_raw=self.get_purchaser_raw_lines(),
            receiver_raw=self.get_receiver_raw_lines(),
            products=self._collect_products(),
            parameter_card=self.get_parameter_card(),
            order_comment=self.get_order_comment(),
            nip=self.get_nip(),
        )

    def _collect_products(self) -> list[AdminOrderProduct]:
        """Read product rows from the order detail table.

        The order products table is inside #order_products.
        Each row: td[1]=product name, td[3]=qty, td[6]=gross unit price.
        Column indices come from live HTML inspection (sf_admin_list table).
        """
        products: list[AdminOrderProduct] = []
        table = self.page.locator("#order_products table.sf_admin_list tbody tr")
        row_count = table.count()
        for i in range(row_count):
            row = table.nth(i)
            cells = row.locator("td")
            cell_count = cells.count()
            if cell_count < 6:
                continue
            try:
                name = cells.nth(0).inner_text(timeout=2_000).strip()
                qty_text = cells.nth(2).inner_text(timeout=2_000).strip()
                price_text = cells.nth(5).inner_text(timeout=2_000).strip()
                qty = int(re.sub(r"[^\d]", "", qty_text) or "0")
                price = _parse_price(price_text)
                if name:
                    products.append(AdminOrderProduct(name=name, quantity=qty, unit_price_gross=price))
            except Exception:  # noqa: BLE001
                continue
        return products

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def change_status(self, status_id: str) -> None:
        """Change order status.

        Clicking #orderStatus > a triggers AJAX that replaces the content of
        #orderStatus with a <select>. Then we select the value and confirm.
        After selection the page reloads automatically.
        """
        self.page.locator(self._LOC_ORDER_STATUS).click()

        status_select = self.page.locator(self._LOC_STATUS_SELECT)
        status_select.wait_for(state="visible", timeout=8_000)
        status_select.select_option(value=status_id)

        # Some status changes trigger a confirm() dialog
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.wait_for_load_state("domcontentloaded", timeout=15_000)
        self.page.locator(self._LOC_PAGE_HEADER).wait_for(state="visible", timeout=10_000)


__all__ = ["AdminOrderDetailPage"]
