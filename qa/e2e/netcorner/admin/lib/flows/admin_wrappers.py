from __future__ import annotations

import re
from decimal import Decimal

from loguru import logger
from playwright.sync_api import Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.admin.lib.config import AdminEnv, resolve_admin_env
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_aggregator_pages import (
    AdminAggregatorCreatePage,
    AdminAggregatorEditPage,
    AdminAggregatorItemCreatePage,
)
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_configuration_page import AdminConfigurationPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_context_page import AdminContextPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_login_page import AdminLoginPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_order_detail_page import AdminOrderDetailPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_orders_page import AdminOrdersPage
from qa.e2e.netcorner.admin.lib.test_data.admin_order_models import AdminOrderData


class AdminWrappers:
    """Orchestration layer for admin panel operations.

    Analogous to CartAndCheckoutWrappers for the frontend.
    Handles login, context selection, and common admin flows.

    Usage in tests:
        admin = AdminWrappers(page, runtime_env)
        admin.open_admin()
        order_data = admin.get_order_data("181255/2026")
        assert order_data.nip == "7770020640", f"NIP mismatch: {order_data.nip}"

    Session management:
        AdminWrappers performs login once per instance. Reuse the same instance
        across multiple operations in a single test to avoid redundant logins.
    """

    def __init__(self, page: Page, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__runtime_env = runtime_env
        self.__admin_env: AdminEnv = resolve_admin_env(runtime_env.server_name)
        self.__logged_in = False

    @property
    def admin_env(self) -> AdminEnv:
        return self.__admin_env

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def open_admin(self) -> None:
        """Navigate to admin panel, login and select PL sales channel context.

        Safe to call multiple times — skips login if already authenticated.
        """
        if self.__logged_in:
            return

        admin_url = f"{self.__admin_env.base_url}/admin.php"
        self.__page.goto(admin_url)
        self.__page.wait_for_load_state("domcontentloaded")

        login_page = AdminLoginPage(self.__page, self.__admin_env.base_url)

        if login_page.is_login_form_visible():
            logger.debug("Admin: performing login as {}", self.__admin_env.login)
            login_page.login(self.__admin_env.login, self.__admin_env.password)
        else:
            logger.debug("Admin: login form not visible, assuming already authenticated")

        context_page = AdminContextPage(self.__page, self.__admin_env.base_url)
        if context_page.is_context_selection_required():
            logger.debug("Admin: selecting sales channel {}", self.__admin_env.sales_channel_id)
            context_page.select_context(self.__admin_env.sales_channel_id)

        self.__logged_in = True
        logger.debug("Admin: session ready at {}", self.__page.url)

    def navigate_to(self, path: str) -> None:
        """Navigate to an arbitrary admin path (login first if needed).

        Args:
            path: Path relative to admin base URL, e.g. 'orders/list/pl'.
                  Leading slash is optional.
        """
        self.open_admin()
        clean_path = path.lstrip("/")
        url = f"{self.__admin_env.base_url}/admin.php/{clean_path}"
        self.__page.goto(url)
        self.__page.wait_for_load_state("domcontentloaded")

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def get_order_data(self, order_number: str) -> AdminOrderData:
        """Navigate to the order detail page and collect all readable data.

        Args:
            order_number: Full order number string, e.g. '181255/2026'.

        Returns:
            AdminOrderData with all fields populated from the admin page.
        """
        self.open_admin()
        orders_page = AdminOrdersPage(self.__page, self.__admin_env.base_url)
        orders_page.navigate_to()
        orders_page.open_order(order_number)

        detail_page = AdminOrderDetailPage(self.__page, self.__admin_env.base_url)
        detail_page.wait_loaded()
        return detail_page.get_all_data(order_number=order_number)

    def assert_order_details(
        self,
        order_number: str,
        *,
        expected_nip: str | None = None,
        expected_summary_price: Decimal | None = None,
        expected_status: str | None = None,
        expected_purchaser_fragments: list[str] | None = None,
    ) -> AdminOrderData:
        """Fetch order data from admin and assert expected values.

        Only fields with non-None expected values are asserted.
        Returns the full AdminOrderData for additional assertions in the test.

        Args:
            order_number: Order number to look up.
            expected_nip: Expected NIP (tax ID) string, digits only.
            expected_summary_price: Expected gross total as Decimal.
            expected_status: Expected order status text.
            expected_purchaser_fragments: Substrings that must appear in purchaser raw lines.
        """
        data = self.get_order_data(order_number)

        if expected_nip is not None:
            actual_nip = re.sub(r"[\s\-]", "", data.nip) if data.nip else ""
            assert actual_nip == expected_nip, (
                f"Zamówienie {order_number}: oczekiwany NIP '{expected_nip}', "
                f"znaleziono '{actual_nip}'."
            )

        if expected_summary_price is not None:
            assert data.summary_price_gross == expected_summary_price, (
                f"Zamówienie {order_number}: oczekiwana cena brutto '{expected_summary_price}', "
                f"znaleziono '{data.summary_price_gross}'."
            )

        if expected_status is not None:
            assert expected_status in data.status, (
                f"Zamówienie {order_number}: oczekiwany status '{expected_status}', "
                f"znaleziono '{data.status}'."
            )

        if expected_purchaser_fragments:
            purchaser_text = "\n".join(data.purchaser_raw)
            for fragment in expected_purchaser_fragments:
                assert fragment in purchaser_text, (
                    f"Zamówienie {order_number}: brak fragmentu '{fragment}' "
                    f"w danych nabywcy:\n{purchaser_text}"
                )

        return data

    def change_order_status(self, order_number: str, status_id: str) -> None:
        """Navigate to the order and change its status.

        Args:
            order_number: Order number to look up.
            status_id: Numeric status ID string as used in admin select option values.
        """
        self.open_admin()
        orders_page = AdminOrdersPage(self.__page, self.__admin_env.base_url)
        orders_page.navigate_to()
        orders_page.open_order(order_number)

        detail_page = AdminOrderDetailPage(self.__page, self.__admin_env.base_url)
        detail_page.wait_loaded()
        detail_page.change_status(status_id)
        logger.debug("Admin: order {} status changed to id={}", order_number, status_id)

    def configure_enforced_shopping_path_postcodes(
        self,
        *,
        ensure_present: list[str] | None = None,
        ensure_absent: list[str] | None = None,
    ) -> list[str]:
        self.open_admin()
        config_page = AdminConfigurationPage(self.__page, self.__admin_env.base_url).navigate_to()
        postcodes = config_page.get_enforced_postcodes()
        normalized = [value.strip() for value in postcodes if value.strip()]

        for value in ensure_present or []:
            candidate = value.strip()
            if candidate and candidate not in normalized:
                normalized.append(candidate)

        for value in ensure_absent or []:
            candidate = value.strip()
            if candidate:
                normalized = [item for item in normalized if item != candidate]

        config_page.set_enforced_postcodes(normalized)
        return normalized

    def create_products_aggregator(
        self,
        *,
        name: str,
        work_name: str,
        url_slug: str,
        item_name: str,
        section_code: str,
        product_codes: str,
        discount_code: str | None = None,
    ) -> str:
        self.open_admin()
        aggregator_id = AdminAggregatorCreatePage(self.__page, self.__admin_env.base_url).navigate_to().create(
            name=name,
            work_name=work_name,
            url_slug=url_slug,
        )
        edit_page = AdminAggregatorEditPage(self.__page, self.__admin_env.base_url, aggregator_id).navigate_to()
        edit_page.open_add_element()
        AdminAggregatorItemCreatePage(self.__page, self.__admin_env.base_url).wait_loaded().create_products_item(
            name=item_name,
            section_code=section_code,
            product_codes=product_codes,
            discount_code=discount_code,
        )
        return f"{self.__runtime_env.base_url}/promocje/{url_slug}"


__all__ = ["AdminWrappers"]
