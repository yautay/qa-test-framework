from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.cart_components import CartProductData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.checkout_components import (
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
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__context = context
        self.__runtime_env = runtime_env

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
                    raise ValueError(
                        "Dla DHL_POP należy wskazać pop_data_id, pop_name lub wybór losowy punktu."
                    )

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
                checkout.content.purchaser.wait_visible().set_electronic_invoice(True)
            case _:
                raise ValueError(f"Nieobsługiwany typ dostawy: {delivery_type}")

        if purchaser_objects is not None:
            if not isinstance(purchaser_objects, CheckoutPurchaserData):
                raise TypeError(
                    "Argument purchaser_objects musi być typu CheckoutPurchaserData."
                )

            checkout.content.purchaser.wait_visible().click_add_data_tile()
            purchaser_overlay = Overlays(self.__page).checkout_purchaser.wait_visible()
            purchaser_overlay.fill_purchaser_data(purchaser_objects)
            purchaser_overlay.click_add_details()
            try:
                purchaser_overlay.wait_hidden(timeout=10_000)
            except AssertionError:
                pass

        if payment_objects is not None:
            if not isinstance(payment_objects, CheckoutPaymentData):
                raise TypeError(
                    "Argument payment_objects musi być typu CheckoutPaymentData."
                )

            payment_methods_component = checkout.content.payment_methods.wait_visible()
            available_payment_methods = payment_methods_component.get_available_payment_methods()

            if payment_objects.payment_method is not None:
                try:
                    payment_surcharge = payment_methods_component.choose_payment_method(payment_objects.payment_method)
                except RuntimeError:
                    payment_surcharge = payment_methods_component.choose_random_available_method()
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
