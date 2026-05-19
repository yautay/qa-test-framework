from __future__ import annotations

from collections.abc import Iterable
from playwright.sync_api import Page

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.setup.models import PromoCodeSeed, PromotionServiceCredentials
from qa.e2e.netcorner.setup.setup_data import DEFAULT_PROMO_CODES, PROMOTION_SERVICE_LOGIN


class NetcornerSetupService:
    _PROMOTION_SAVE_SELECTOR = "#form-buttons button.btn-success, input[value='Zapisz'], input[type='submit'][name='save']"
    _B2B_REQUIRED_ERROR = (
        "Występowanie promocji musi być zdefiniowane. Jeżeli wybrano kanał komputronik.pl, "
        "należy również wybrać b2b.komputronik.pl"
    )
    _DATES_LOCKED_ERROR = "Nie możesz zmienić daty rozpoczęcia i zakończenia istniejącej promocji"

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

        normalized_base_url = promotions_base_url.rstrip("/")

        self._page.goto(normalized_base_url, wait_until="domcontentloaded")
        login = self._page.locator("#inputUsername, input[name='login'], #login").first
        password = self._page.locator("#inputPassword, input[name='password'], #password").first
        submit = self._page.locator("button[type='submit'], input[type='submit']").first

        if login.count() > 0 and password.count() > 0:
            login.fill(credentials.login)
            password.fill(credentials.password)
            submit.click()
            self._page.wait_for_load_state("domcontentloaded")

        for promotion_id in promotion_ids:
            self._page.goto(f"{normalized_base_url}/promotion/edit/{promotion_id}", wait_until="domcontentloaded")
            self._set_promotion_service_occurrence_window()
            self._scroll_to_promotion_occurrence_section()
            self._page.wait_for_timeout(2_000)
            self._page.locator(self._PROMOTION_SAVE_SELECTOR).first.click()
            self._page.wait_for_timeout(2_000)
            self._page.wait_for_load_state("domcontentloaded")
            error_text = self._get_danger_alert_text()
            if error_text and self._B2B_REQUIRED_ERROR in error_text:
                self._ensure_b2b_sales_channel_in_purpose()
                self._scroll_to_promotion_occurrence_section()
                self._page.locator(self._PROMOTION_SAVE_SELECTOR).first.click()
                self._page.wait_for_timeout(2_000)
                self._page.wait_for_load_state("domcontentloaded")
                error_text = self._get_danger_alert_text()

            if error_text and self._DATES_LOCKED_ERROR in error_text:
                continue

            if error_text:
                raise AssertionError(
                    "Promotion service save failed for promotion_id="
                    f"{promotion_id}: {error_text}"
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

        self._set_mx_datepicker_value("occurrence_date_from", date_from)
        self._set_mx_datepicker_value("occurrence_time_from", time_from)
        self._set_mx_datepicker_value("occurrence_date_to", date_to)
        self._set_mx_datepicker_value("occurrence_time_to", time_to)

    def _set_mx_datepicker_value(self, picker_id: str, value: str) -> None:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        self._page.locator(f"#{picker_id}").first.evaluate(
            """
            (root, rawValue) => {
              const vm = root.__vue__;
              if (vm) {
                vm.currentValue = rawValue;
                if (typeof vm.$emit === 'function') {
                  vm.$emit('input', rawValue);
                  vm.$emit('change', rawValue);
                }
              }

              const visibleInput = root.querySelector('input.mx-input');
              if (visibleInput) {
                visibleInput.value = rawValue;
                visibleInput.dispatchEvent(new Event('input', { bubbles: true }));
                visibleInput.dispatchEvent(new Event('change', { bubbles: true }));
              }
            }
            """,
            value,
        )

    def _compute_promotion_window(self) -> tuple[str, str, str, str]:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        window = self._page.evaluate(
            """
            () => {
              const pad = (n) => String(n).padStart(2, '0');
              const fmtDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
              const fmtTime = (d) => `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

              const start = new Date(Date.now() + 2 * 60 * 1000);
              const end = new Date(start);
              end.setMonth(end.getMonth() + 1);

              return {
                dateFrom: fmtDate(start),
                timeFrom: fmtTime(start),
                dateTo: fmtDate(end),
                timeTo: fmtTime(end),
              };
            }
            """
        )
        return window["dateFrom"], window["timeFrom"], window["dateTo"], window["timeTo"]

    def _scroll_to_promotion_occurrence_section(self) -> None:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        self._page.locator("#purpose_purpose").first.scroll_into_view_if_needed()

    def _get_danger_alert_text(self) -> str | None:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        danger_alert = self._page.locator(".alert.alert-danger").first
        if danger_alert.count() > 0 and danger_alert.is_visible():
            return danger_alert.inner_text().strip()
        return None

    def _ensure_b2b_sales_channel_in_purpose(self) -> None:
        if self._page is None:
            raise ValueError("Page jest wymagana dla setupu promotion-service.")

        purpose_group = self._page.locator("#purpose_purpose").first
        purpose_group.wait_for(state="visible")

        selected_b2b = purpose_group.locator(".vue-treeselect__multi-value-label", has_text="b2b.komputronik.pl")
        if selected_b2b.count() > 0:
            return

        result = purpose_group.locator(".vue-treeselect").first.evaluate(
            """
            (el) => {
              const vm = el.__vue__;
              if (!vm) {
                return { ok: false, reason: "vue_instance_missing" };
              }

              const walk = (nodes, out = []) => {
                for (const node of nodes || []) {
                  out.push(node);
                  if (node.children && node.children.length) walk(node.children, out);
                }
                return out;
              };

              const allNodes = walk(vm.forest?.normalizedOptions || []);
              const b2bNode = allNodes.find((n) => (n.label || "").trim() === "b2b.komputronik.pl");
              if (!b2bNode) {
                return {
                  ok: false,
                  reason: "b2b_option_missing",
                  labels: allNodes.map((n) => n.label).filter(Boolean).slice(0, 120),
                };
              }

              const selectedIds = new Set((vm.internalValue || []).map((n) => n.id));
              if (!selectedIds.has(b2bNode.id)) {
                vm.select(b2bNode);
              }

              return {
                ok: true,
                selectedIds: (vm.internalValue || []).map((n) => n.id),
              };
            }
            """
        )

        if not result.get("ok"):
            reason = result.get("reason", "unknown")
            labels = result.get("labels")
            raise AssertionError(
                "Nie udalo sie dodac kanalu b2b.komputronik.pl w 'Wystepowanie promocji' "
                f"(reason={reason}, labels={labels})."
            )

        selected_b2b.wait_for(state="visible")
