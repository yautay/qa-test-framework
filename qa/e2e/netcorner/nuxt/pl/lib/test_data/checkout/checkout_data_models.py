from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeliveryTypes(Enum):
    INPOST = "inpost"
    DHL_POP = "dhl_pop"
    COURIER_SERVICE = "courier_service"
    STORE_PICKUP = "store_pickup"


class PaymentMethods(Enum):
    BLIK = "blik"
    PREPAID_TRANSFER = "prepaid_transfer"
    CASH_ON_DELIVERY_CASH = "cash_on_delivery_cash"
    CASH_ON_DELIVERY_CARD = "cash_on_delivery_card"


class PaymentRequiredConsent(Enum):
    REGULATION = "regulation"


@dataclass(frozen=True)
class CheckoutDeliveryCase:
    case_id: str
    delivery_type: DeliveryTypes
    delivery_objects: DeliveryObjects | None = None
    purchaser_objects: PurchaserObjects | None = None
    payment_objects: PaymentObjects | None = None


class DeliveryObjects:
    pass


@dataclass
class DeliveryCourierReceiverData(DeliveryObjects):
    first_name: str
    surname: str
    street_name: str
    street_number: str
    postal_code: str
    city: str
    phone_number: str
    email: str
    company_name: str | None = None
    is_company: bool = False
    delivery_type: DeliveryTypes = DeliveryTypes.COURIER_SERVICE


@dataclass
class DeliveryStorehouseReceiverData(DeliveryObjects):
    postal_code: str | None = None
    city: str | None = None
    storehouse_name: str | None = None
    storehouse_data_id: str | None = None
    choose_random_storehouse: bool = True
    delivery_type: DeliveryTypes = DeliveryTypes.STORE_PICKUP


@dataclass
class DeliveryDhlPopReceiverData(DeliveryObjects):
    postal_code: str | None = None
    city: str | None = None
    pop_name: str | None = None
    pop_data_id: str | None = None
    choose_random_pop_point: bool = True
    delivery_type: DeliveryTypes = DeliveryTypes.DHL_POP


@dataclass
class DeliveryInpostReceiverData(DeliveryObjects):
    postal_code: str | None = None
    city: str | None = None
    locker_code: str | None = None
    inpost_point_name: str | None = None
    inpost_point_data_id: str | None = None
    choose_random_inpost_point: bool = True
    delivery_type: DeliveryTypes = DeliveryTypes.INPOST


class PurchaserObjects:
    pass


@dataclass
class CheckoutPurchaserData(PurchaserObjects):
    first_name: str
    surname: str
    street_name: str
    street_number: str
    postal_code: str
    city: str
    phone_number: str
    email: str
    copy_data_from_receiver: bool = False
    is_company: bool = False
    company_name: str | None = None
    tax_identification_number: str | None = None


class PaymentObjects:
    pass


@dataclass
class CheckoutPaymentData(PaymentObjects):
    payment_method: PaymentMethods | None = None
    comment: str | None = None
    required_consent: bool = False
