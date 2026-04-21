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
    DeliveryObjects,
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
        cart.footer.click_continue()
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
            case DeliveryTypes.DHL_POP:
                checkout.content.delivery_type.click_dhl_tile()
            case DeliveryTypes.INPOST:
                checkout.content.delivery_type.click_inpost_tile()
            case DeliveryTypes.COURIER_SERVICE:
                checkout.content.delivery_type.click_courier_tile()
                checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
                if not isinstance(delivery_objects, DeliveryCourierReceiverData):
                    raise TypeError(
                        "Dla COURIER_SERVICE argument delivery_objects musi być typu DeliveryCourierReceiverData."
                    )
                Overlays(self.__page).checkout_courier_receiver.wait_visible().fill_receiver_data(delivery_objects)
                checkout.content.delivery_methods.wait_visible().get_methods_layout()
                checkout.content.delivery_methods.choose_random_available_method()
                checkout.content.purchaser.wait_visible().set_electronic_invoice(True)
            case _:
                raise ValueError(f"Nieobsługiwany typ dostawy: {delivery_type}")

        if purchaser_objects is not None:
            if not isinstance(purchaser_objects, CheckoutPurchaserData):
                raise TypeError(
                    "Argument purchaser_objects musi być typu CheckoutPurchaserData."
                )

            checkout.content.purchaser.wait_visible().click_add_data_tile()
            Overlays(self.__page).checkout_purchaser.wait_visible().fill_purchaser_data(purchaser_objects).click_add_details()

        if payment_objects is not None:
            if not isinstance(payment_objects, CheckoutPaymentData):
                raise TypeError(
                    "Argument payment_objects musi być typu CheckoutPaymentData."
                )

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

        summary_data = checkout.content.summary.wait_visible().click_place_order()
        typ_summary_data = checkout.content.typ_summary.wait_visible().get_summary_data()
        return CheckoutProcessData(
            delivery_types_aviable=delivery_types_aviable,
            available_payment_methods=available_payment_methods,
            payment_surcharge=payment_surcharge,
            summary_data=summary_data,
            typ_summary_data=typ_summary_data,
        )
