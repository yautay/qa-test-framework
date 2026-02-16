from __future__ import annotations

import os
from typing import Any

from qa.e2e.netcorner.nuxt.pl.app.data.orders_smoke_data import (
    DEFAULT_PURCHASER,
    DEFAULT_RECEIVER,
    OrderAs,
    OrderSmokeCase,
    PaymentKind,
)
from qa.e2e.netcorner.nuxt.pl.app.pages.auth_page import AuthPage
from qa.e2e.netcorner.nuxt.pl.app.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.app.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.app.pages.layer_page import LayerPage
from qa.e2e.netcorner.nuxt.pl.app.pages.product_list_page import ProductListPage
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_provider_factory import (
    ReceiverProviderFactory,
)
from qa.e2e.netcorner.nuxt.pl.app.pages.thank_you_page import ThankYouPage


class OrderFlowService:
    def __init__(self, page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.product_list_page = ProductListPage(page, base_url)
        self.layer_page = LayerPage(page)
        self.cart_page = CartPage(page, base_url)
        self.auth_page = AuthPage(page)
        self.checkout_page = CheckoutPage(page, base_url)
        self.receiver_provider_factory = ReceiverProviderFactory(self.checkout_page)
        self.thank_you_page = ThankYouPage(page)

    def run_full_checkout(self, case: OrderSmokeCase) -> dict[str, Any]:
        self.product_list_page.page.goto(self.base_url)
        self.product_list_page.dismiss_cookie_banner()

        for idx, category_path in enumerate(case.category_paths):
            self.product_list_page.open_category(category_path)
            self.product_list_page.dismiss_cookie_banner()
            if "digital" in case.case_id and idx == 0:
                self.product_list_page.apply_digital_filter_if_visible()
            if not self.product_list_page.add_buyable_product_to_cart():
                self.product_list_page.search_product(case.search_phrase)
                self.product_list_page.dismiss_cookie_banner()
                if not self.product_list_page.add_buyable_product_to_cart():
                    raise AssertionError(f"Could not add buyable product to cart from {category_path}")
            self.layer_page.close_recommendation_if_visible()
            self.layer_page.go_to_cart_if_visible()

        self.cart_page.open()
        assert self.cart_page.has_interactive_cart_surface(), "Cart surface not visible"
        assert self.cart_page.move_further_to_checkout(), "Could not continue from cart to checkout"

        self._resolve_auth_step(case.order_as)

        assert self.checkout_page.has_interactive_checkout_surface(), "Checkout surface not visible"
        self._fill_checkout(case)

        assert self.checkout_page.submit_order(), "Could not submit order"
        order_number = self.thank_you_page.wait_for_order_number()
        assert order_number, "Thank-you order number is empty"
        assert self.thank_you_page.has_summary_price(), "Thank-you summary price not visible"
        return {"order_number": order_number}

    def _resolve_auth_step(self, order_as: OrderAs) -> None:
        if order_as == OrderAs.NON_REGISTERED:
            self.auth_page.continue_without_registration()
            return

        login = os.getenv("SMOKE_LOGIN")
        password = os.getenv("SMOKE_PASSWORD")
        if login and password:
            if not self.auth_page.try_login(login, password):
                self.auth_page.continue_without_registration()
            return

        self.auth_page.continue_without_registration()

    def _fill_checkout(self, case: OrderSmokeCase) -> None:
        provider = self.receiver_provider_factory.build(case.delivery_kind)
        provider.apply(
            ReceiverSelectionRequest(
                delivery_kind=case.delivery_kind.value,
                receiver_data=DEFAULT_RECEIVER.__dict__,
                delivery_location=case.delivery_location,
                delivery_point_name=case.delivery_point_name,
            )
        )

        self.checkout_page.fill_receiver_data(DEFAULT_PURCHASER.__dict__)
        self.checkout_page.select_payment(self._payment_label(case.payment_kind))
        self.checkout_page.accept_all_visible_terms()

    @staticmethod
    def _payment_label(payment_kind: PaymentKind) -> str:
        if payment_kind == PaymentKind.CASH:
            return "Gotówka"
        return "Przelew"
