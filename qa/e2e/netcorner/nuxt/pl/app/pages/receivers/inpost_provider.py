from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.pickup_provider import PickupReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest


class InpostReceiverProvider(PickupReceiverProvider):
    def apply(self, request: ReceiverSelectionRequest) -> None:
        super().apply(request)
