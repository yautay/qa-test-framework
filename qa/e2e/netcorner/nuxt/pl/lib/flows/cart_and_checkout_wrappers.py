from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal

from loguru import logger
from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.cart_components import CartProductData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.checkout import (
    CheckoutSummaryData,
    DeliveryTypeData,
    PaymentMethodData,
    TypSummaryData,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    CheckoutPaymentData,
    CheckoutPurchaserData,
    DeliveryCourierReceiverData,
    DeliveryDhlPopReceiverData,
    DeliveryInpostReceiverData,
    DeliveryObjects,
    DeliveryStorehouseReceiverData,
    DeliveryTypes,
    PaymentObjects,
    PaymentRequiredConsent,
    PurchaserObjects,
)


@dataclass(frozen=True, slots=True)
class CheckoutProcessData:
    delivery_types_aviable: DeliveryTypeData
    available_payment_methods: list[PaymentMethodData]
    payment_surcharge: Decimal
    summary_data: CheckoutSummaryData
    typ_summary_data: TypSummaryData


class CartAndCheckoutWrappers:
    DELIVERY_PROVIDER_STABILITY_WINDOW_MS = 2_500
    DELIVERY_PROVIDER_STABILITY_POLL_MS = 100

    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__context = context
        self.__runtime_env = runtime_env

    @staticmethod
    def __expected_delivery_provider(delivery_type: DeliveryTypes) -> str:
        mapping = {
            DeliveryTypes.STORE_PICKUP: "storehouse",
            DeliveryTypes.DHL_POP: "dhl",
            DeliveryTypes.INPOST: "inpost",
        }
        return mapping.get(delivery_type, "")

    def __assert_selected_delivery_provider(self, checkout: CheckoutPage, delivery_type: DeliveryTypes) -> None:
        expected_provider = self.__expected_delivery_provider(delivery_type)
        if not expected_provider:
            return

        delivery_type_component = checkout.content.delivery_type.wait_visible()

        actual_provider = ""
        provider_error = ""
        try:
            actual_provider = delivery_type_component.get_selected_delivery_provider(timeout=8_000)
        except RuntimeError as exc:
            provider_error = str(exc)

        actual_provider_token = actual_provider or "<unknown>"
        if actual_provider_token != expected_provider:
            logger.error(
                "TEST_ERROR code=DELIVERY_TYPE_CHANGED_AFTER_PICKUP expected_provider={} actual_provider={} "
                "delivery_type={} page_url={} error={}",
                expected_provider,
                actual_provider_token,
                delivery_type.value,
                self.__page.url,
                provider_error,
            )
            raise AssertionError(
                "Wybrany typ dostawy zmienił się po zamknięciu modala punktu odbioru: "
                f"oczekiwano '{expected_provider}', a wykryto '{actual_provider_token}'."
            )

        stability_start = time.monotonic()
        stability_deadline = stability_start + (self.DELIVERY_PROVIDER_STABILITY_WINDOW_MS / 1000)
        while time.monotonic() < stability_deadline:
            try:
                stable_provider = delivery_type_component.get_selected_delivery_provider(timeout=1_000)
            except RuntimeError as exc:
                elapsed_ms = int(max(0.0, time.monotonic() - stability_start) * 1000)
                logger.error(
                    "TEST_ERROR code=DELIVERY_PROVIDER_UNREADABLE_AFTER_PICKUP expected_provider={} actual_provider={} "
                    "delivery_type={} page_url={} elapsed_ms={} error={}",
                    expected_provider,
                    "<unknown>",
                    delivery_type.value,
                    self.__page.url,
                    elapsed_ms,
                    str(exc),
                )
                raise AssertionError(
                    "Nie udało się odczytać aktywnego typu dostawy po zamknięciu modala punktu odbioru."
                ) from exc

            if stable_provider != expected_provider:
                elapsed_ms = int(max(0.0, time.monotonic() - stability_start) * 1000)
                logger.error(
                    "TEST_ERROR code=DELIVERY_PROVIDER_DRIFT_AFTER_PICKUP expected_provider={} actual_provider={} "
                    "delivery_type={} page_url={} elapsed_ms={}",
                    expected_provider,
                    stable_provider or "<unknown>",
                    delivery_type.value,
                    self.__page.url,
                    elapsed_ms,
                )
                raise AssertionError(
                    "Typ dostawy zmienił się po krótkim czasie od zamknięcia modala punktu odbioru: "
                    f"oczekiwano '{expected_provider}', a wykryto '{stable_provider or '<unknown>'}'."
                )

            self.__page.wait_for_timeout(self.DELIVERY_PROVIDER_STABILITY_POLL_MS)

    def process_cart(self) -> dict[str, CartProductData]:
        cart = CartPage(self.__page, self.__runtime_env.base_url).wait_loaded()
        cart_data = cart.content.cart.get_data()
        cart.proceed_to_checkout()
        return cart_data

    def process_checkout(
        self,
        delivery_type: DeliveryTypes,
        delivery_objects: DeliveryObjects | None = None,
        purchaser_objects: PurchaserObjects | None = None,
        payment_objects: PaymentObjects | None = None,
    ) -> CheckoutProcessData:
        checkout = CheckoutPage(self.__page, self.__runtime_env.base_url).wait_loaded()
        checkout.content.delivery_type.wait_visible()
        delivery_types_aviable = checkout.content.delivery_type.get_delivery_type_availability()
        available_payment_methods: list[PaymentMethodData] = []
        payment_surcharge = Decimal("0.00")

        match delivery_type:
            case DeliveryTypes.STORE_PICKUP:
                checkout.content.delivery_type.click_storehouse_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryStorehouseReceiverData):
                    raise TypeError(
                        "Dla STORE_PICKUP argument delivery_objects musi być typu DeliveryStorehouseReceiverData."
                    )

                search_value = next(
                    (
                        value.strip()
                        for value in (delivery_objects.postal_code, delivery_objects.city)
                        if value and value.strip()
                    ),
                    "",
                )
                if not search_value:
                    raise ValueError("Dla STORE_PICKUP wymagany jest kod pocztowy lub miasto do wyszukiwania salonu.")

                storehouse_overlay = Overlays(self.__page).checkout_storehouse_receiver.wait_visible()
                storehouse_overlay.search_storehouses(search_value)
                if delivery_objects.storehouse_data_id:
                    storehouse_overlay.choose_storehouse_by_data_id(delivery_objects.storehouse_data_id)
                elif delivery_objects.storehouse_name:
                    storehouse_overlay.choose_storehouse_by_name(delivery_objects.storehouse_name)
                elif delivery_objects.choose_random_storehouse:
                    storehouse_overlay.choose_random_storehouse()
                else:
                    raise ValueError(
                        "Dla STORE_PICKUP należy wskazać storehouse_data_id, storehouse_name lub wybór losowy salonu."
                    )
                self.__assert_selected_delivery_provider(checkout, DeliveryTypes.STORE_PICKUP)

            case DeliveryTypes.DHL_POP:
                checkout.content.delivery_type.click_dhl_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryDhlPopReceiverData):
                    raise TypeError("Dla DHL_POP argument delivery_objects musi być typu DeliveryDhlPopReceiverData.")

                search_value = next(
                    (
                        value.strip()
                        for value in (delivery_objects.postal_code, delivery_objects.city)
                        if value and value.strip()
                    ),
                    "",
                )
                if not search_value:
                    raise ValueError("Dla DHL_POP wymagany jest kod pocztowy lub miasto do wyszukiwania punktu.")

                dhl_pop_overlay = Overlays(self.__page).checkout_dhl_pop_receiver.wait_visible()
                dhl_pop_overlay.search_pop_points(search_value)
                if delivery_objects.pop_data_id:
                    dhl_pop_overlay.choose_pop_point_by_data_id(delivery_objects.pop_data_id)
                elif delivery_objects.pop_name:
                    dhl_pop_overlay.choose_pop_point_by_name(delivery_objects.pop_name)
                elif delivery_objects.choose_random_pop_point:
                    dhl_pop_overlay.choose_random_pop_point()
                else:
                    raise ValueError("Dla DHL_POP należy wskazać pop_data_id, pop_name lub wybór losowy punktu.")
                self.__assert_selected_delivery_provider(checkout, DeliveryTypes.DHL_POP)

            case DeliveryTypes.INPOST:
                checkout.content.delivery_type.click_inpost_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryInpostReceiverData):
                    raise TypeError("Dla INPOST argument delivery_objects musi być typu DeliveryInpostReceiverData.")

                search_value = next(
                    (
                        value.strip()
                        for value in (delivery_objects.locker_code, delivery_objects.postal_code, delivery_objects.city)
                        if value and value.strip()
                    ),
                    "",
                )
                if not search_value:
                    raise ValueError("Dla INPOST wymagany jest kod paczkomatu, kod pocztowy lub miasto.")

                inpost_overlay = Overlays(self.__page).checkout_inpost_receiver.wait_visible()
                inpost_overlay.search_inpost_points(search_value)
                if delivery_objects.inpost_point_data_id:
                    inpost_overlay.choose_inpost_point_by_data_id(delivery_objects.inpost_point_data_id)
                elif delivery_objects.inpost_point_name:
                    inpost_overlay.choose_inpost_point_by_name(delivery_objects.inpost_point_name)
                elif delivery_objects.choose_random_inpost_point:
                    inpost_overlay.choose_random_inpost_point()
                else:
                    raise ValueError(
                        "Dla INPOST należy wskazać inpost_point_data_id, inpost_point_name lub wybór losowy punktu."
                    )
                self.__assert_selected_delivery_provider(checkout, DeliveryTypes.INPOST)

            case DeliveryTypes.COURIER_SERVICE:
                checkout.content.delivery_type.click_courier_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryCourierReceiverData):
                    raise TypeError(
                        "Dla COURIER_SERVICE argument delivery_objects musi być typu DeliveryCourierReceiverData."
                    )
                courier_overlay = Overlays(self.__page).checkout_courier_receiver.wait_visible()
                courier_overlay.fill_receiver_data(delivery_objects)
                courier_overlay.click_add_details()
                courier_overlay.wait_hidden(timeout=10_000)

                delivery_methods = checkout.content.delivery_methods.wait_visible().wait_for_available_methods(
                    timeout=10_000
                )
                delivery_methods.get_methods_layout()
                delivery_methods.choose_random_available_method()
            case _:
                raise ValueError(f"Nieobsługiwany typ dostawy: {delivery_type}")

        checkout.content.purchaser.wait_visible().set_electronic_invoice(True)

        if not isinstance(purchaser_objects, CheckoutPurchaserData):
            raise TypeError("Argument purchaser_objects musi być typu CheckoutPurchaserData.")

        checkout.content.purchaser.wait_visible().click_add_data_tile()
        purchaser_overlay = Overlays(self.__page).checkout_purchaser.wait_visible()
        purchaser_overlay.fill_purchaser_data(purchaser_objects)
        purchaser_overlay.click_add_details()
        purchaser_overlay.wait_hidden(timeout=10_000)

        if not isinstance(payment_objects, CheckoutPaymentData):
            raise TypeError("Argument payment_objects musi być typu CheckoutPaymentData.")

        payment_methods_component = checkout.content.payment_methods.wait_visible()
        available_payment_methods = payment_methods_component.get_available_payment_methods()

        if payment_objects.payment_method is not None:
            payment_surcharge = payment_methods_component.choose_payment_method(payment_objects.payment_method)
        else:
            payment_surcharge = payment_methods_component.choose_random_available_method()

        if payment_objects.comment:
            payment_methods_component.set_order_comment(payment_objects.comment)

        if payment_objects.required_consent:
            payment_methods_component.set_required_consent(PaymentRequiredConsent.REGULATION)

        summary_data, typ_summary_data = checkout.submit_order()
        return CheckoutProcessData(
            delivery_types_aviable=delivery_types_aviable,
            available_payment_methods=available_payment_methods,
            payment_surcharge=payment_surcharge,
            summary_data=summary_data,
            typ_summary_data=typ_summary_data,
        )

    def process_checkout_steps_only(
        self,
        delivery_type: DeliveryTypes,
        delivery_objects: DeliveryObjects | None = None,
        purchaser_objects: PurchaserObjects | None = None,
        payment_objects: PaymentObjects | None = None,
    ) -> CheckoutSummaryData:
        """Run all checkout steps (delivery, purchaser, payment) without submitting the order.

        Returns the ``CheckoutSummaryData`` captured when the summary section becomes visible
        (i.e. the "Zamawiam z obowiązkiem zapłaty" button is present and clickable).
        The order is NOT placed.  Use this for monitoring/smoke scenarios that verify the full
        checkout path is reachable without consuming real order capacity.
        """
        # Delegate full flow to process_checkout but intercept just before submit.
        # We replicate the steps inline to avoid coupling to submit path.
        checkout = CheckoutPage(self.__page, self.__runtime_env.base_url).wait_loaded()
        checkout.content.delivery_type.wait_visible()

        match delivery_type:
            case DeliveryTypes.STORE_PICKUP:
                checkout.content.delivery_type.click_storehouse_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryStorehouseReceiverData):
                    raise TypeError(
                        "Dla STORE_PICKUP argument delivery_objects musi być typu DeliveryStorehouseReceiverData."
                    )
                search_value = next(
                    (v.strip() for v in (delivery_objects.postal_code, delivery_objects.city) if v and v.strip()),
                    "",
                )
                storehouse_overlay = Overlays(self.__page).checkout_storehouse_receiver.wait_visible()
                storehouse_overlay.search_storehouses(search_value)
                if delivery_objects.storehouse_data_id:
                    storehouse_overlay.choose_storehouse_by_data_id(delivery_objects.storehouse_data_id)
                elif delivery_objects.storehouse_name:
                    storehouse_overlay.choose_storehouse_by_name(delivery_objects.storehouse_name)
                else:
                    storehouse_overlay.choose_random_storehouse()
                self.__assert_selected_delivery_provider(checkout, DeliveryTypes.STORE_PICKUP)

            case DeliveryTypes.DHL_POP:
                checkout.content.delivery_type.click_dhl_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryDhlPopReceiverData):
                    raise TypeError("Dla DHL_POP argument delivery_objects musi być typu DeliveryDhlPopReceiverData.")
                search_value = next(
                    (v.strip() for v in (delivery_objects.postal_code, delivery_objects.city) if v and v.strip()),
                    "",
                )
                dhl_pop_overlay = Overlays(self.__page).checkout_dhl_pop_receiver.wait_visible()
                dhl_pop_overlay.search_pop_points(search_value)
                if delivery_objects.pop_data_id:
                    dhl_pop_overlay.choose_pop_point_by_data_id(delivery_objects.pop_data_id)
                elif delivery_objects.pop_name:
                    dhl_pop_overlay.choose_pop_point_by_name(delivery_objects.pop_name)
                else:
                    dhl_pop_overlay.choose_random_pop_point()
                self.__assert_selected_delivery_provider(checkout, DeliveryTypes.DHL_POP)

            case DeliveryTypes.INPOST:
                checkout.content.delivery_type.click_inpost_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryInpostReceiverData):
                    raise TypeError("Dla INPOST argument delivery_objects musi być typu DeliveryInpostReceiverData.")
                search_value = next(
                    (
                        v.strip()
                        for v in (delivery_objects.locker_code, delivery_objects.postal_code, delivery_objects.city)
                        if v and v.strip()
                    ),
                    "",
                )
                inpost_overlay = Overlays(self.__page).checkout_inpost_receiver.wait_visible()
                inpost_overlay.search_inpost_points(search_value)
                if delivery_objects.inpost_point_data_id:
                    inpost_overlay.choose_inpost_point_by_data_id(delivery_objects.inpost_point_data_id)
                elif delivery_objects.inpost_point_name:
                    inpost_overlay.choose_inpost_point_by_name(delivery_objects.inpost_point_name)
                else:
                    inpost_overlay.choose_random_inpost_point()
                self.__assert_selected_delivery_provider(checkout, DeliveryTypes.INPOST)

            case DeliveryTypes.COURIER_SERVICE:
                checkout.content.delivery_type.click_courier_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryCourierReceiverData):
                    raise TypeError(
                        "Dla COURIER_SERVICE argument delivery_objects musi być typu DeliveryCourierReceiverData."
                    )
                courier_overlay = Overlays(self.__page).checkout_courier_receiver.wait_visible()
                courier_overlay.fill_receiver_data(delivery_objects)
                courier_overlay.click_add_details()
                courier_overlay.wait_hidden(timeout=10_000)
                delivery_methods = checkout.content.delivery_methods.wait_visible().wait_for_available_methods(
                    timeout=10_000
                )
                delivery_methods.choose_random_available_method()

            case _:
                raise ValueError(f"Nieobsługiwany typ dostawy: {delivery_type}")

        checkout.content.purchaser.wait_visible().set_electronic_invoice(True)
        if not isinstance(purchaser_objects, CheckoutPurchaserData):
            raise TypeError("Argument purchaser_objects musi być typu CheckoutPurchaserData.")
        checkout.content.purchaser.wait_visible().click_add_data_tile()
        purchaser_overlay = Overlays(self.__page).checkout_purchaser.wait_visible()
        purchaser_overlay.fill_purchaser_data(purchaser_objects)
        purchaser_overlay.click_add_details()
        purchaser_overlay.wait_hidden(timeout=10_000)

        if not isinstance(payment_objects, CheckoutPaymentData):
            raise TypeError("Argument payment_objects musi być typu CheckoutPaymentData.")
        payment_methods_component = checkout.content.payment_methods.wait_visible()
        if payment_objects.payment_method is not None:
            payment_methods_component.choose_payment_method(payment_objects.payment_method)
        else:
            payment_methods_component.choose_random_available_method()
        if payment_objects.comment:
            payment_methods_component.set_order_comment(payment_objects.comment)
        if payment_objects.required_consent:
            payment_methods_component.set_required_consent(PaymentRequiredConsent.REGULATION)

        return checkout.content.summary.wait_visible().wait_place_order_button_visible()
