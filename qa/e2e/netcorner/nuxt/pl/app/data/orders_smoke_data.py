from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OrderAs(str, Enum):
    REGISTERED = "registered"
    LOGGED_IN_CART = "logged_in_cart"
    NON_REGISTERED = "non_registered"


class DeliveryKind(str, Enum):
    COURIER = "courier"
    STOREHOUSE = "storehouse"
    DIGITAL = "digital"


class PaymentKind(str, Enum):
    ELECTRONIC_TRANSFER = "electronic_transfer"
    CASH = "cash"


@dataclass(frozen=True)
class AddressData:
    name: str
    surname: str
    phone: str
    email: str
    postal_code: str
    city: str
    street_name: str
    street_number: str
    company: str


@dataclass(frozen=True)
class OrderSmokeCase:
    case_id: str
    scenario: str
    order_as: OrderAs
    category_paths: tuple[str, ...]
    delivery_kind: DeliveryKind
    payment_kind: PaymentKind
    search_phrase: str
    delivery_location: str | None = None
    delivery_point_name: str | None = None


DEFAULT_RECEIVER = AddressData(
    name="Janusz",
    surname="Odbiorca",
    phone="500600700",
    email="janusz.odbiorca@test.netcorner.pl",
    postal_code="61-693",
    city="Poznan",
    street_name="Wolczynska",
    street_number="37/1",
    company="Janusz Odbiorca Company",
)


DEFAULT_PURCHASER = AddressData(
    name="Jan",
    surname="Nabywca",
    phone="500600700",
    email="jan.nabywca@test.netcorner.pl",
    postal_code="61-693",
    city="Poznan",
    street_name="Wolczynska",
    street_number="37/1",
    company="Jan Nabywca Company",
)


ORDER_SMOKE_CASES: tuple[OrderSmokeCase, ...] = (
    OrderSmokeCase(
        case_id="delivery_at_home_registered",
        scenario="delivery home registered",
        order_as=OrderAs.REGISTERED,
        category_paths=("category/6569/klawiatury-pc.html",),
        delivery_kind=DeliveryKind.COURIER,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="klawiatura",
    ),
    OrderSmokeCase(
        case_id="delivery_at_home_logged_in_cart",
        scenario="delivery home logged in cart",
        order_as=OrderAs.LOGGED_IN_CART,
        category_paths=("category/6569/klawiatury-pc.html",),
        delivery_kind=DeliveryKind.COURIER,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="klawiatura",
    ),
    OrderSmokeCase(
        case_id="delivery_at_home_non_registered",
        scenario="delivery home non registered",
        order_as=OrderAs.NON_REGISTERED,
        category_paths=("category/6569/klawiatury-pc.html",),
        delivery_kind=DeliveryKind.COURIER,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="klawiatura",
    ),
    OrderSmokeCase(
        case_id="self_pickup_registered",
        scenario="self pickup registered",
        order_as=OrderAs.REGISTERED,
        category_paths=("category/6569/klawiatury-pc.html",),
        delivery_kind=DeliveryKind.STOREHOUSE,
        payment_kind=PaymentKind.CASH,
        search_phrase="klawiatura",
        delivery_location="60-001",
        delivery_point_name="Poznan Outlet",
    ),
    OrderSmokeCase(
        case_id="self_pickup_logged_in_cart",
        scenario="self pickup logged in cart",
        order_as=OrderAs.LOGGED_IN_CART,
        category_paths=("category/6569/klawiatury-pc.html",),
        delivery_kind=DeliveryKind.STOREHOUSE,
        payment_kind=PaymentKind.CASH,
        search_phrase="klawiatura",
        delivery_location="60-001",
        delivery_point_name="Poznan Outlet",
    ),
    OrderSmokeCase(
        case_id="self_pickup_non_registered",
        scenario="self pickup non registered",
        order_as=OrderAs.NON_REGISTERED,
        category_paths=("category/6569/klawiatury-pc.html",),
        delivery_kind=DeliveryKind.STOREHOUSE,
        payment_kind=PaymentKind.CASH,
        search_phrase="klawiatura",
        delivery_location="60-001",
        delivery_point_name="Poznan Outlet",
    ),
    OrderSmokeCase(
        case_id="digital_licence_registered",
        scenario="digital registered",
        order_as=OrderAs.REGISTERED,
        category_paths=("category/5808/oprogramowanie.html",),
        delivery_kind=DeliveryKind.DIGITAL,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="licencja",
    ),
    OrderSmokeCase(
        case_id="digital_licence_non_registered",
        scenario="digital non registered",
        order_as=OrderAs.NON_REGISTERED,
        category_paths=("category/5808/oprogramowanie.html",),
        delivery_kind=DeliveryKind.DIGITAL,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="licencja",
    ),
    OrderSmokeCase(
        case_id="mixed_licence_with_product_registered",
        scenario="mixed digital and physical registered",
        order_as=OrderAs.REGISTERED,
        category_paths=("category/5808/oprogramowanie.html", "category/6569/klawiatury-pc.html"),
        delivery_kind=DeliveryKind.COURIER,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="licencja",
    ),
    OrderSmokeCase(
        case_id="mixed_licence_with_product_non_registered",
        scenario="mixed digital and physical non registered",
        order_as=OrderAs.NON_REGISTERED,
        category_paths=("category/5808/oprogramowanie.html", "category/6569/klawiatury-pc.html"),
        delivery_kind=DeliveryKind.COURIER,
        payment_kind=PaymentKind.ELECTRONIC_TRANSFER,
        search_phrase="licencja",
    ),
)
