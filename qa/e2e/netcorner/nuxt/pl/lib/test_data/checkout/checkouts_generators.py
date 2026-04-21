from __future__ import annotations

import uuid

from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    CheckoutDeliveryCase,
    CheckoutPurchaserData,
    DeliveryCourierReceiverData,
    DeliveryTypes,
)


class DeliveryCourierReceiverDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._first_name = "Jan"
        self._surname = "Odbiorca"
        self._street_name = "Dluga"
        self._street_number = "10A/12"
        self._postal_code = "00-001"
        self._city = "Warszawa"
        self._phone_number = "791233545"
        self._email = f"receiver_{unique}@test.pl"
        self._company_name = f"Odbiorca {unique} Sp. z o.o."
        self._is_company = False
        self._delivery_type = DeliveryTypes.COURIER_SERVICE

    def with_company(self) -> DeliveryCourierReceiverDataBuilder:
        self._is_company = True
        return self

    def with_delivery_type(self, delivery_type: DeliveryTypes) -> DeliveryCourierReceiverDataBuilder:
        self._delivery_type = delivery_type
        return self

    def build(self) -> DeliveryCourierReceiverData:
        return DeliveryCourierReceiverData(
            first_name=self._first_name,
            surname=self._surname,
            street_name=self._street_name,
            street_number=self._street_number,
            postal_code=self._postal_code,
            city=self._city,
            phone_number=self._phone_number,
            email=self._email,
            company_name=self._company_name,
            is_company=self._is_company,
            delivery_type=self._delivery_type,
        )


def private_person_delivery_courier_receiver() -> DeliveryCourierReceiverData:
    return DeliveryCourierReceiverDataBuilder().build()


def company_delivery_courier_receiver() -> DeliveryCourierReceiverData:
    return DeliveryCourierReceiverDataBuilder().with_company().build()


class CheckoutPurchaserDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._first_name = "Jan"
        self._surname = "Nabywca"
        self._company_name = f"Nabywca {unique} Sp. z o.o."
        self._tax_identification_number = "7770020640"
        self._street_name = "Dluga"
        self._street_number = "10A/12"
        self._postal_code = "00-001"
        self._city = "Warszawa"
        self._phone_number = "791233545"
        self._email = f"purchaser_{unique}@test.pl"
        self._copy_data_from_receiver = False
        self._is_company = False

    def with_company(self) -> CheckoutPurchaserDataBuilder:
        self._is_company = True
        return self

    def with_copy_data_from_receiver(self) -> CheckoutPurchaserDataBuilder:
        self._copy_data_from_receiver = True
        return self

    def build(self) -> CheckoutPurchaserData:
        common_data = {
            "first_name": self._first_name,
            "surname": self._surname,
            "street_name": self._street_name,
            "street_number": self._street_number,
            "postal_code": self._postal_code,
            "city": self._city,
            "phone_number": self._phone_number,
            "email": self._email,
            "copy_data_from_receiver": self._copy_data_from_receiver,
        }

        if self._is_company:
            return CheckoutPurchaserData(
                **common_data,
                is_company=True,
                company_name=self._company_name,
                tax_identification_number=self._tax_identification_number,
            )

        return CheckoutPurchaserData(**common_data, is_company=False)

    def build_private_person(self) -> CheckoutPurchaserData:
        self._is_company = False
        return CheckoutPurchaserData(
            first_name=self._first_name,
            surname=self._surname,
            street_name=self._street_name,
            street_number=self._street_number,
            postal_code=self._postal_code,
            city=self._city,
            phone_number=self._phone_number,
            email=self._email,
            copy_data_from_receiver=self._copy_data_from_receiver,
            is_company=False,
        )

    def build_company(self) -> CheckoutPurchaserData:
        self._is_company = True
        return CheckoutPurchaserData(
            first_name=self._first_name,
            surname=self._surname,
            street_name=self._street_name,
            street_number=self._street_number,
            postal_code=self._postal_code,
            city=self._city,
            phone_number=self._phone_number,
            email=self._email,
            copy_data_from_receiver=self._copy_data_from_receiver,
            is_company=True,
            company_name=self._company_name,
            tax_identification_number=self._tax_identification_number,
        )


def private_person_checkout_purchaser() -> CheckoutPurchaserData:
    return CheckoutPurchaserDataBuilder().build_private_person()


def company_checkout_purchaser() -> CheckoutPurchaserData:
    return CheckoutPurchaserDataBuilder().build_company()


def delivery_types() -> list[DeliveryTypes]:
    return [
        DeliveryTypes.COURIER_SERVICE,
        DeliveryTypes.DHL_POP,
        DeliveryTypes.INPOST,
        DeliveryTypes.STORE_PICKUP,
    ]


def checkout_delivery_cases() -> list[CheckoutDeliveryCase]:
    return [
        CheckoutDeliveryCase(
            case_id="courier_service",
            delivery_type=DeliveryTypes.COURIER_SERVICE,
            delivery_objects=private_person_delivery_courier_receiver(),
            purchaser_objects=private_person_checkout_purchaser(),
        ),
        CheckoutDeliveryCase(case_id="dhl_pop", delivery_type=DeliveryTypes.DHL_POP),
        CheckoutDeliveryCase(case_id="inpost", delivery_type=DeliveryTypes.INPOST),
        CheckoutDeliveryCase(case_id="store_pickup", delivery_type=DeliveryTypes.STORE_PICKUP),
    ]
