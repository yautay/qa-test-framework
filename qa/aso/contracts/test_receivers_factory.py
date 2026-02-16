from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.app.data.orders_smoke_data import DeliveryKind
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.courier_provider import CourierReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.dhlpop_provider import DhlPopReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.digital_provider import DigitalReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.inpost_provider import InpostReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.lift_provider import LiftReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.pickup_provider import PickupReceiverProvider
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_models import ReceiverSelectionRequest
from qa.e2e.netcorner.nuxt.pl.app.pages.receivers.receiver_provider_factory import (
    ReceiverProviderFactory,
)

pytestmark = [pytest.mark.aso]


class _CheckoutPageSpy:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def select_delivery_kind(self, delivery_kind: str) -> None:
        self.calls.append(("select_delivery_kind", delivery_kind))

    def fill_receiver_data(self, receiver_data: dict[str, str]) -> None:
        self.calls.append(("fill_receiver_data", receiver_data))

    def choose_pickup_details(self, location: str | None, point_name: str | None) -> None:
        self.calls.append(("choose_pickup_details", location, point_name))

    def select_lift_option_if_available(self, with_lift: bool) -> None:
        self.calls.append(("select_lift_option_if_available", with_lift))


@pytest.mark.parametrize(
    ("delivery_kind", "expected_type"),
    [
        (DeliveryKind.COURIER, CourierReceiverProvider),
        (DeliveryKind.STOREHOUSE, PickupReceiverProvider),
        (DeliveryKind.DIGITAL, DigitalReceiverProvider),
        ("inpost", InpostReceiverProvider),
        ("dhlpop", DhlPopReceiverProvider),
        ("courier_with_lift", LiftReceiverProvider),
        ("courier_without_lift", LiftReceiverProvider),
    ],
)
def test_receiver_factory_builds_expected_provider(delivery_kind, expected_type):
    factory = ReceiverProviderFactory(_CheckoutPageSpy())
    provider = factory.build(delivery_kind)
    assert isinstance(provider, expected_type)


def test_receiver_factory_rejects_unsupported_delivery_kind():
    factory = ReceiverProviderFactory(_CheckoutPageSpy())
    with pytest.raises(ValueError, match="Unsupported delivery_kind"):
        factory.build("rocket_ship")


def test_courier_provider_applies_receiver_data():
    checkout = _CheckoutPageSpy()
    provider = CourierReceiverProvider(checkout)
    request = ReceiverSelectionRequest(delivery_kind="courier", receiver_data={"name": "Jan"})

    provider.apply(request)

    assert checkout.calls == [
        ("select_delivery_kind", "courier"),
        ("fill_receiver_data", {"name": "Jan"}),
    ]


def test_pickup_provider_applies_pickup_selection():
    checkout = _CheckoutPageSpy()
    provider = PickupReceiverProvider(checkout)
    request = ReceiverSelectionRequest(
        delivery_kind="storehouse",
        receiver_data={"name": "Jan"},
        delivery_location="60-001",
        delivery_point_name="Poznan Outlet",
    )

    provider.apply(request)

    assert checkout.calls == [
        ("select_delivery_kind", "storehouse"),
        ("choose_pickup_details", "60-001", "Poznan Outlet"),
    ]


def test_lift_provider_selects_lift_variant():
    checkout = _CheckoutPageSpy()
    provider = LiftReceiverProvider(checkout, with_lift=True)
    request = ReceiverSelectionRequest(delivery_kind="courier_with_lift",
                                       receiver_data={"name": "Jan"})

    provider.apply(request)

    assert checkout.calls == [
        ("select_delivery_kind", "courier"),
        ("fill_receiver_data", {"name": "Jan"}),
        ("select_lift_option_if_available", True),
    ]
