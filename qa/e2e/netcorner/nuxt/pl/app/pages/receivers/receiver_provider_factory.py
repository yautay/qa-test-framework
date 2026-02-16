from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.data.orders_smoke_data import DeliveryKind
from qa.e2e.netcorner.nuxt.pl.app.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.base_provider import BaseReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.courier_provider import CourierReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.dhlpop_provider import DhlPopReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.digital_provider import DigitalReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.inpost_provider import InpostReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.lift_provider import LiftReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.pickup_provider import PickupReceiverProvider


class ReceiverProviderFactory:
    def __init__(self, checkout_page: CheckoutPage) -> None:
        self.checkout_page = checkout_page

    def build(self, delivery_kind: DeliveryKind | str) -> BaseReceiverProvider:
        kind = delivery_kind.value if isinstance(delivery_kind, DeliveryKind) else str(delivery_kind)

        if kind == DeliveryKind.STOREHOUSE.value:
            return PickupReceiverProvider(self.checkout_page)
        if kind == DeliveryKind.INPOST.value:
            return InpostReceiverProvider(self.checkout_page)
        if kind == DeliveryKind.DHLPOP.value:
            return DhlPopReceiverProvider(self.checkout_page)
        if kind == DeliveryKind.COURIER_BIG_SIZE_WITH_lIFT.value:
            return LiftReceiverProvider(self.checkout_page, with_lift=True)
        if kind == DeliveryKind.COURIER_BIG_SIZE_WITHOUT_lIFT.value:
            return LiftReceiverProvider(self.checkout_page, with_lift=False)
        if kind == DeliveryKind.DIGITAL.value:
            return DigitalReceiverProvider(self.checkout_page)
        if kind == DeliveryKind.COURIER.value:
            return CourierReceiverProvider(self.checkout_page)
        raise ValueError(f"Unsupported delivery_kind: {kind}")
