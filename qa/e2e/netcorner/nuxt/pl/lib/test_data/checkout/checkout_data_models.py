from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeliveryTypes(Enum):
    INPOST = "inpost"
    DHL_POP = "dhl_pop"
    COURIER_SERVICE = "courier_service"
    STORE_PICKUP = "store_pickup"


@dataclass(frozen=True)
class CheckoutDeliveryCase:
    case_id: str
    delivery_type: DeliveryTypes
    delivery_objects: DeliveryObjects | None = None
    purchaser_objects: PurchaserObjects | None = None


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
