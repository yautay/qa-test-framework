from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.base_provider import BaseReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest


class DigitalReceiverProvider(BaseReceiverProvider):
    def apply(self, request: ReceiverSelectionRequest) -> None:
        self.checkout_page.select_delivery_kind(request.delivery_kind)
        self.checkout_page.fill_receiver_data(request.receiver_data)
