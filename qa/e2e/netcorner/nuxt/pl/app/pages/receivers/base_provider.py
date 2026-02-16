from __future__ import annotations

from abc import ABC, abstractmethod

from qa.e2e.netcorner.nuxt.pl.app.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest


class BaseReceiverProvider(ABC):
    def __init__(self, checkout_page: CheckoutPage) -> None:
        self.checkout_page = checkout_page

    @abstractmethod
    def apply(self, request: ReceiverSelectionRequest) -> None:
        """Apply receiver selection/fill logic for delivery method."""
