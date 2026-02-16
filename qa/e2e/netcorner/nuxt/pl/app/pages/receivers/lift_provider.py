from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.base_provider import BaseReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest


class LiftReceiverProvider(BaseReceiverProvider):
    def __init__(self, checkout_page, with_lift: bool) -> None:
        super().__init__(checkout_page)
        self.with_lift = with_lift

    def apply(self, request: ReceiverSelectionRequest) -> None:
        self.checkout_page.select_delivery_kind("courier")
        self.checkout_page.fill_receiver_data(request.receiver_data)
        self.checkout_page.select_lift_option_if_available(with_lift=self.with_lift)
