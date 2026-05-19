from __future__ import annotations

from collections.abc import Iterable
from calendar import monthrange
from datetime import datetime, timedelta

from playwright.sync_api import Page

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.setup.models import PromoCodeSeed, PromotionServiceCredentials
from qa.e2e.netcorner.setup.setup_data import DEFAULT_PROMO_CODES, PROMOTION_SERVICE_LOGIN


class NetcornerSetupService:
    def __init__(self, admin_panel: AdminWrappers | None, page: Page | None = None) -> None:
        self._admin = admin_panel
        self._page = page

    def ensure_promo_codes(self, promo_codes: Iterable[PromoCodeSeed] = DEFAULT_PROMO_CODES) -> None:
        if self._admin is None:
            raise ValueError("AdminWrappers jest wymagany dla setupu kodów promocyjnych.")
        for promo in promo_codes:
            self._admin.ensure_promo_code(
                code=promo.code,
                promotion_name=promo.promotion_name,
                type_label=promo.type_label,
            )

    def recompute_product_purchase_eligibility(self, product_ids: Iterable[int]) -> None:
        if self._admin is None:
            raise ValueError("AdminWrappers jest wymagany dla setupu produktów.")
        for product_id in sorted(product_ids):
            self._admin.save_product(product_id)

    def save_existing_sezam_promotions(self, product_ids: Iterable[int]) -> None:
        if self._admin is None:
            raise ValueError("AdminWrappers jest wymagany dla setupu promocji Sezam.")
        for product_id in sorted(product_ids):
            self._admin.save_existing_product_promotion(product_id)

    def reindex_products(self, product_ids: Iterable[int]) -> list[str]:
        if self._admin is None:
            raise ValueError("AdminWrappers jest wymagany dla indeksowania produktów.")
        erp_codes: list[str] = []
        for product_id in sorted(product_ids):
            codes = self._admin.get_product_codes(product_id)
            erp_code = codes.get("erp_code")
            if erp_code:
                erp_codes.append(erp_code)
        self._admin.reindex_products_by_erp_codes(erp_codes)
        return erp_codes

    def save_promotions_service(
        self,
        promotions_base_url: str,
        promotion_ids: Iterable[str],
        credentials: PromotionServiceCredentials = PROMOTION_SERVICE_LOGIN,
    ) -> None:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        self._page.goto(promotions_base_url, wait_until="domcontentloaded")
        login = self._page.locator("#inputUsername, input[name='login'], #login").first
        password = self._page.locator("#inputPassword, input[name='password'], #password").first
        submit = self._page.locator("button[type='submit'], input[type='submit']").first

        if login.count() > 0 and password.count() > 0:
            login.fill(credentials.login)
            password.fill(credentials.password)
            submit.click()
            self._page.wait_for_load_state("domcontentloaded")

        for promotion_id in promotion_ids:
            self._page.goto(f"{promotions_base_url}/promotion/edit/{promotion_id}", wait_until="domcontentloaded")
            self._set_promotion_service_occurrence_window()
            self._page.wait_for_timeout(2_000)
            self._page.locator("#form-buttons button.btn-success, input[value='Zapisz'], input[type='submit'][name='save']").first.click()
            self._page.wait_for_load_state("domcontentloaded")
            danger_alert = self._page.locator(".alert.alert-danger").first
            if danger_alert.count() > 0 and danger_alert.is_visible():
                raise AssertionError(
                    f"Promotion service save failed for promotion_id={promotion_id}: widoczny komunikat alert-danger."
                )

    def _set_promotion_service_occurrence_window(self) -> None:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        date_from, time_from, date_to, time_to = self._compute_promotion_window()
        values = {
            "occurrence_date_from": date_from,
            "occurrence_time_from": time_from,
            "occurrence_date_to": date_to,
            "occurrence_time_to": time_to,
        }

        for field_name, field_value in values.items():
            input_locator = self._page.locator(f"input[name='{field_name}']").first
            input_locator.wait_for(state="attached")
            input_locator.evaluate(
                """
                (el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                field_value,
            )

    @staticmethod
    def _compute_promotion_window() -> tuple[str, str, str, str]:
        promotion_start = (datetime.now() + timedelta(minutes=1)).replace(microsecond=0)

        promotion_end = NetcornerSetupService._add_calendar_month(promotion_start)
        return (
            promotion_start.strftime("%Y-%m-%d"),
            promotion_start.strftime("%H:%M:%S"),
            promotion_end.strftime("%Y-%m-%d"),
            promotion_end.strftime("%H:%M:%S"),
        )

    @staticmethod
    def _add_calendar_month(dt: datetime) -> datetime:
        year = dt.year + (dt.month // 12)
        month = (dt.month % 12) + 1
        day = min(dt.day, monthrange(year, month)[1])
        return dt.replace(year=year, month=month, day=day)
