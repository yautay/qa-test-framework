from __future__ import annotations

import re
from decimal import Decimal

from loguru import logger
from playwright.sync_api import Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.admin.lib.config import AdminEnv, resolve_admin_env
from qa.e2e.netcorner.admin.lib.timeouts import SLOW_OPERATION_MS
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_aggregator_pages import (
    AdminAggregatorCreatePage,
    AdminAggregatorEditPage,
    AdminAggregatorItemCreatePage,
)
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_configuration_page import AdminConfigurationPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_context_page import AdminContextPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import (
    AdminCartOfferPage,
    AdminEmployeeProgramPage,
    AdminProductOzoPage,
    EmployeeProgramGroupData,
)
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_login_page import AdminLoginPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_order_detail_page import AdminOrderDetailPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_orders_page import AdminOrdersPage
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_promo_code_page import AdminPromoCodePage
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

        admin_url = f"{self.__admin_env.base_url}"
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

    def get_order_status_options(self, order_number: str):
        self.open_admin()
        orders_page = AdminOrdersPage(self.__page, self.__admin_env.base_url)
        orders_page.navigate_to()
        orders_page.open_order(order_number)

        detail_page = AdminOrderDetailPage(self.__page, self.__admin_env.base_url)
        detail_page.wait_loaded()
        return detail_page.get_status_options()

    def get_order_products_raw_text(self, order_number: str) -> str:
        self.open_admin()
        orders_page = AdminOrdersPage(self.__page, self.__admin_env.base_url)
        orders_page.navigate_to()
        orders_page.open_order(order_number)

        detail_page = AdminOrderDetailPage(self.__page, self.__admin_env.base_url)
        detail_page.wait_loaded()
        return detail_page.get_order_products_raw_text()

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

    def save_product(self, product_id: int) -> None:
        self.navigate_to(f"product/edit/pl/product_id/{product_id}")
        save_button = self.__page.locator("input.sf_admin_action_save").first
        save_button.click()
        self.__page.wait_for_load_state("domcontentloaded")

    def save_existing_product_promotion(self, product_id: int) -> None:
        self.navigate_to(f"product/edit/pl/product_id/{product_id}")
        promotions_tab = self.__page.locator("a[href='#ui-tabs-1']").first
        promotions_tab.click()
        self.__page.locator("#ui-tabs-1 table").first.wait_for(state="visible", timeout=SLOW_OPERATION_MS)
        edit_button = self.__page.locator("#ui-tabs-1 a:has(img[alt='Edit_icon'])").first
        if edit_button.count() == 0:
            return
        edit_button.click()
        save_promotion = self.__page.locator("#ui-tabs-1 input[name='submit_promotion']").first
        save_promotion.click()
        self.__page.wait_for_load_state("domcontentloaded")

    def get_product_codes(self, product_id: int) -> dict[str, str | None]:
        self.navigate_to(f"product/edit/pl/product_id/{product_id}")
        codes_text = self.__page.locator("#editHeaderProductCodes").first.inner_text()
        product_match = re.search(r"Kod produktu:\s*([^,]+)", codes_text)
        erp_match = re.search(r"Kod produktu ERP:\s*([^,]+)", codes_text)
        producer_match = re.search(r"Kod producenta produktu:\s*([^,]+)", codes_text)
        return {
            "product_code": product_match.group(1).strip() if product_match else None,
            "erp_code": erp_match.group(1).strip() if erp_match else None,
            "producer_code": producer_match.group(1).strip() if producer_match else None,
        }

    def reindex_products_by_erp_codes(self, erp_codes: list[str]) -> None:
        self.navigate_to("searchProductsIndex/update/pl")
        textarea = self.__page.locator("#product_codes").first
        textarea.fill("\n".join(erp_codes))
        self.__page.locator("input[value='Indeksuj']").first.click()
        self.__page.locator("div.save-ok").first.wait_for(state="visible", timeout=120_000)

    def ensure_aggregator_promo_code(
        self,
        *,
        code: str,
        promotion_name: str = "TESTKODAGREGATOR 1PLN BRUTTO",
    ) -> None:
        self.ensure_promo_code(code=code, promotion_name=promotion_name)

    def ensure_promo_code(
        self,
        *,
        code: str,
        promotion_name: str,
        type_label: str = "Promocja",
    ) -> None:
        self.open_admin()
        AdminPromoCodePage(self.__page, self.__admin_env.base_url).ensure_promo_code(
            code=code,
            promotion_name=promotion_name,
            type_label=type_label,
        )


    # ------------------------------------------------------------------
    # Cart Offer
    # ------------------------------------------------------------------

    def create_cart_offer_and_send_email(
        self,
        *,
        product_id: int | str,
        qty: int = 1,
        recipient_email: str,
        channel_id: str = "1",
        price_type_id: str = "1",
        price_category_id: str | None = None,
        fixed_price: str | None = None,
        expiration_days: int = 7,
    ) -> str:
        """Create a cart offer in admin and send it via email.

        Args:
            product_id: Admin product identifier (ID/ERP depending on page search mode).
            qty: Product quantity in offer.
            recipient_email: Email to send the offer to.
            channel_id: Sales channel value (default '1').
            price_type_id: '1' = fixed price, other = dynamic.
            price_category_id: Optional price category value.
            fixed_price: Fixed brutto price string (for static offers).
            expiration_days: Days until offer expires.

        Returns:
            The admin edit-page URL (contains offer id) after save.
        """
        self.open_admin()
        cart_offer_page = AdminCartOfferPage(self.__page, self.__admin_env.base_url)
        cart_offer_page.navigate_to_create()
        offer_url = cart_offer_page.create_cart_offer(
            product_id=product_id,
            qty=qty,
            recipient_email=recipient_email,
            channel_id=channel_id,
            price_type_id=price_type_id,
            price_category_id=price_category_id,
            fixed_price=fixed_price,
            expiration_days=expiration_days,
        )
        # After save, send the offer email from the edit page
        cart_offer_page.send_offer_email()
        logger.debug("Admin: cart offer created and sent to {} from url={}", recipient_email, offer_url)
        return offer_url

    # ------------------------------------------------------------------
    # Employee Program (Partner Groups)
    # ------------------------------------------------------------------

    def create_employee_group(self, data: EmployeeProgramGroupData) -> str:
        """Create a partner/employee group in admin.

        Args:
            data: EmployeeProgramGroupData with group configuration.

        Returns:
            The group ID string extracted from the redirect URL.
        """
        self.open_admin()
        emp_page = AdminEmployeeProgramPage(self.__page, self.__admin_env.base_url)
        emp_page.navigate_to_create()
        group_id = emp_page.create_group(data)
        logger.debug("Admin: employee group '{}' created, id={}", data.group_name, group_id)
        return group_id

    def delete_employee_group(self, group_id: str) -> None:
        """Delete a partner/employee group by ID.

        Args:
            group_id: The group ID string to delete.
        """
        self.open_admin()
        emp_page = AdminEmployeeProgramPage(self.__page, self.__admin_env.base_url)
        emp_page.delete_group(group_id)
        logger.debug("Admin: employee group id={} deleted", group_id)

    def get_employee_group_sms_hashes(self, group_id: str) -> list[str]:
        """Navigate to the employee group edit page and return the SMS hashes.

        Args:
            group_id: The group ID string.

        Returns:
            List of SMS hash strings.
        """
        self.open_admin()
        emp_page = AdminEmployeeProgramPage(self.__page, self.__admin_env.base_url)
        emp_page.navigate_to_edit(group_id)
        return emp_page.get_sms_hashes()

    def generate_employee_group_qr(self, group_id: str) -> None:
        """Navigate to the employee group edit page and generate a new QR code.

        Args:
            group_id: The group ID string.
        """
        self.open_admin()
        emp_page = AdminEmployeeProgramPage(self.__page, self.__admin_env.base_url)
        emp_page.navigate_to_edit(group_id)
        emp_page.generate_new_qr_code()
        logger.debug("Admin: QR code regenerated for employee group id={}", group_id)

    def get_employee_group_qr_value(self, group_id: str) -> str:
        """Navigate to the employee group edit page and read QR value.

        Args:
            group_id: The group ID string.

        Returns:
            QR registration value (URL or encoded payload source).
        """
        self.open_admin()
        emp_page = AdminEmployeeProgramPage(self.__page, self.__admin_env.base_url)
        emp_page.navigate_to_edit(group_id)
        value = emp_page.get_qr_code_value()
        logger.debug("Admin: QR value read for employee group id={} (len={})", group_id, len(value))
        return value

    def reset_ozo_for_product(self, product_id: int, *, per_customer: int = 5) -> None:
        """Reset OZO (limited-sale) counters for a product to a clean test state.

        Deactivates all currently active promotions on the product and creates
        a fresh one with default test parameters (sold=3, total=50, per_customer=1).

        Args:
            product_id: Admin product ID for the OZO test product.
        """
        self.open_admin()
        ozo_page = AdminProductOzoPage(self.__page, self.__admin_env.base_url, product_id)
        ozo_page.navigate_to()
        ozo_page.reset_ozo_promotion(per_customer=per_customer)
        logger.debug("Admin: OZO promotion reset for product_id={} per_customer={}", product_id, per_customer)

    def get_ozo_limited_sale_settings(self, product_id: int) -> dict[str, int | str]:
        """Read active OZO limited-sale settings for product from admin promotions tab."""
        self.open_admin()
        ozo_page = AdminProductOzoPage(self.__page, self.__admin_env.base_url, product_id)
        ozo_page.navigate_to()
        return ozo_page.get_limited_sale_settings()


__all__ = ["AdminWrappers"]
