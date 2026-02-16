from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.base_provider import BaseReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest


class PickupReceiverProvider(BaseReceiverProvider):
    def apply(self, request: ReceiverSelectionRequest) -> None:
        self.checkout_page.select_delivery_kind(request.delivery_kind)
        self.checkout_page.choose_pickup_details(request.delivery_location, request.delivery_point_name)
