from __future__ import annotations

import uuid

from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    CheckoutDeliveryCase,
    CheckoutPaymentData,
    CheckoutPurchaserData,
    DeliveryCourierReceiverData,
    DeliveryDhlPopReceiverData,
    DeliveryInpostReceiverData,
    DeliveryStorehouseReceiverData,
    DeliveryTypes,
    PaymentMethods,
)


class DeliveryCourierReceiverDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._first_name = "Jan"
        self._surname = "Odbiorca"
        self._street_name = "Dluga"
        self._street_number = "10A/12"
        self._postal_code = "60-001"
        self._city = "Poznań"
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


class DeliveryStorehouseReceiverDataBuilder:
    def __init__(self) -> None:
        self._postal_code = "62-090"
        self._city = "Poznań"
        self._storehouse_name: str | None = None
        self._storehouse_data_id: str | None = None
        self._choose_random_storehouse = True
        self._delivery_type = DeliveryTypes.STORE_PICKUP

    def with_postal_code(self, postal_code: str) -> DeliveryStorehouseReceiverDataBuilder:
        self._postal_code = postal_code
        return self

    def with_city(self, city: str) -> DeliveryStorehouseReceiverDataBuilder:
        self._city = city
        return self

    def with_storehouse_name(self, storehouse_name: str) -> DeliveryStorehouseReceiverDataBuilder:
        self._storehouse_name = storehouse_name
        self._storehouse_data_id = None
        self._choose_random_storehouse = False
        return self

    def with_storehouse_data_id(self, storehouse_data_id: str) -> DeliveryStorehouseReceiverDataBuilder:
        self._storehouse_data_id = storehouse_data_id
        self._storehouse_name = None
        self._choose_random_storehouse = False
        return self

    def with_random_storehouse(self, enabled: bool = True) -> DeliveryStorehouseReceiverDataBuilder:
        self._choose_random_storehouse = enabled
        return self

    def build(self) -> DeliveryStorehouseReceiverData:
        return DeliveryStorehouseReceiverData(
            postal_code=self._postal_code,
            city=self._city,
            storehouse_name=self._storehouse_name,
            storehouse_data_id=self._storehouse_data_id,
            choose_random_storehouse=self._choose_random_storehouse,
            delivery_type=self._delivery_type,
        )


def private_person_delivery_storehouse_receiver() -> DeliveryStorehouseReceiverData:
    return DeliveryStorehouseReceiverDataBuilder().build()


class DeliveryDhlPopReceiverDataBuilder:
    def __init__(self) -> None:
        self._postal_code = "62-090"
        self._city = "Poznań"
        self._pop_name: str | None = None
        self._pop_data_id: str | None = None
        self._choose_random_pop_point = True
        self._delivery_type = DeliveryTypes.DHL_POP

    def with_postal_code(self, postal_code: str) -> DeliveryDhlPopReceiverDataBuilder:
        self._postal_code = postal_code
        return self

    def with_city(self, city: str) -> DeliveryDhlPopReceiverDataBuilder:
        self._city = city
        return self

    def with_pop_name(self, pop_name: str) -> DeliveryDhlPopReceiverDataBuilder:
        self._pop_name = pop_name
        self._pop_data_id = None
        self._choose_random_pop_point = False
        return self

    def with_pop_data_id(self, pop_data_id: str) -> DeliveryDhlPopReceiverDataBuilder:
        self._pop_data_id = pop_data_id
        self._pop_name = None
        self._choose_random_pop_point = False
        return self

    def with_random_pop_point(self, enabled: bool = True) -> DeliveryDhlPopReceiverDataBuilder:
        self._choose_random_pop_point = enabled
        return self

    def build(self) -> DeliveryDhlPopReceiverData:
        return DeliveryDhlPopReceiverData(
            postal_code=self._postal_code,
            city=self._city,
            pop_name=self._pop_name,
            pop_data_id=self._pop_data_id,
            choose_random_pop_point=self._choose_random_pop_point,
            delivery_type=self._delivery_type,
        )


def private_person_delivery_dhl_pop_receiver() -> DeliveryDhlPopReceiverData:
    return DeliveryDhlPopReceiverDataBuilder().build()


class DeliveryInpostReceiverDataBuilder:
    def __init__(self) -> None:
        self._postal_code = "62-090"
        self._city = "Poznań"
        self._locker_code: str | None = None
        self._inpost_point_name: str | None = None
        self._inpost_point_data_id: str | None = None
        self._choose_random_inpost_point = True
        self._delivery_type = DeliveryTypes.INPOST

    def with_postal_code(self, postal_code: str) -> DeliveryInpostReceiverDataBuilder:
        self._postal_code = postal_code
        return self

    def with_city(self, city: str) -> DeliveryInpostReceiverDataBuilder:
        self._city = city
        return self

    def with_locker_code(self, locker_code: str) -> DeliveryInpostReceiverDataBuilder:
        self._locker_code = locker_code
        return self

    def with_point_name(self, point_name: str) -> DeliveryInpostReceiverDataBuilder:
        self._inpost_point_name = point_name
        self._inpost_point_data_id = None
        self._choose_random_inpost_point = False
        return self

    def with_point_data_id(self, point_data_id: str) -> DeliveryInpostReceiverDataBuilder:
        self._inpost_point_data_id = point_data_id
        self._inpost_point_name = None
        self._choose_random_inpost_point = False
        return self

    def with_random_inpost_point(self, enabled: bool = True) -> DeliveryInpostReceiverDataBuilder:
        self._choose_random_inpost_point = enabled
        return self

    def build(self) -> DeliveryInpostReceiverData:
        return DeliveryInpostReceiverData(
            postal_code=self._postal_code,
            city=self._city,
            locker_code=self._locker_code,
            inpost_point_name=self._inpost_point_name,
            inpost_point_data_id=self._inpost_point_data_id,
            choose_random_inpost_point=self._choose_random_inpost_point,
            delivery_type=self._delivery_type,
        )


def private_person_delivery_inpost_receiver() -> DeliveryInpostReceiverData:
    return DeliveryInpostReceiverDataBuilder().build()


class CheckoutPurchaserDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._first_name = "Jan"
        self._surname = "Nabywca"
        self._company_name = f"Nabywca {unique} Sp. z o.o."
        self._tax_identification_number = "7770020640"
        self._street_name = "Dluga"
        self._street_number = "10A/12"
        self._postal_code = "60-001"
        self._city = "Poznań"
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


class CheckoutPaymentDataBuilder:
    def __init__(self) -> None:
        self._payment_method: PaymentMethods | None = None
        self._comment: str | None = None
        self._required_consent: bool = False

    def with_payment_method(self, payment_method: PaymentMethods) -> CheckoutPaymentDataBuilder:
        self._payment_method = payment_method
        return self

    def with_blik(self) -> CheckoutPaymentDataBuilder:
        self._payment_method = PaymentMethods.BLIK
        return self

    def with_prepaid_transfer(self) -> CheckoutPaymentDataBuilder:
        self._payment_method = PaymentMethods.PREPAID_TRANSFER
        return self

    def with_cash_on_delivery_cash(self) -> CheckoutPaymentDataBuilder:
        self._payment_method = PaymentMethods.CASH_ON_DELIVERY_CASH
        return self

    def with_cash_on_pick_up(self) -> CheckoutPaymentDataBuilder:
        self._payment_method = PaymentMethods.CASH_ON_PICK_UP
        return self

    def with_cash_on_delivery_card(self) -> CheckoutPaymentDataBuilder:
        self._payment_method = PaymentMethods.CASH_ON_DELIVERY_CARD
        return self

    def with_comment(self, comment: str) -> CheckoutPaymentDataBuilder:
        self._comment = comment
        return self

    def with_required_consent(self, enabled: bool = True) -> CheckoutPaymentDataBuilder:
        self._required_consent = enabled
        return self

    def with_required_terms(self) -> CheckoutPaymentDataBuilder:
        return self.with_required_consent(True)

    def build(self) -> CheckoutPaymentData:
        return CheckoutPaymentData(
            payment_method=self._payment_method,
            comment=self._comment,
            required_consent=self._required_consent,
        )


def checkout_payment_blik_required_terms() -> CheckoutPaymentData:
    return CheckoutPaymentDataBuilder().with_blik().with_required_terms().build()

def checkout_payment_cash_on_pickup_required_terms() -> CheckoutPaymentData:
    return CheckoutPaymentDataBuilder().with_cash_on_pick_up().with_required_terms().build()


def checkout_payment_prepaid_transfer_required_terms() -> CheckoutPaymentData:
    return CheckoutPaymentDataBuilder().with_prepaid_transfer().with_required_terms().build()


def checkout_payment_cash_on_delivery_cash_required_terms() -> CheckoutPaymentData:
    return CheckoutPaymentDataBuilder().with_cash_on_delivery_cash().with_required_terms().build()


def checkout_payment_cash_on_delivery_card_required_terms() -> CheckoutPaymentData:
    return CheckoutPaymentDataBuilder().with_cash_on_delivery_card().with_required_terms().build()


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
            payment_objects=checkout_payment_blik_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="dhl_pop",
            delivery_type=DeliveryTypes.DHL_POP,
            delivery_objects=private_person_delivery_dhl_pop_receiver(),
            purchaser_objects=private_person_checkout_purchaser(),
            payment_objects=checkout_payment_blik_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="inpost",
            delivery_type=DeliveryTypes.INPOST,
            delivery_objects=private_person_delivery_inpost_receiver(),
            purchaser_objects=private_person_checkout_purchaser(),
            payment_objects=checkout_payment_blik_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="store_pickup",
            delivery_type=DeliveryTypes.STORE_PICKUP,
            delivery_objects=private_person_delivery_storehouse_receiver(),
            purchaser_objects=private_person_checkout_purchaser(),
            payment_objects=checkout_payment_cash_on_pickup_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="courier_service_company",
            delivery_type=DeliveryTypes.COURIER_SERVICE,
            delivery_objects=company_delivery_courier_receiver(),
            purchaser_objects=company_checkout_purchaser(),
            payment_objects=checkout_payment_blik_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="dhl_pop_company",
            delivery_type=DeliveryTypes.DHL_POP,
            delivery_objects=private_person_delivery_dhl_pop_receiver(),
            purchaser_objects=company_checkout_purchaser(),
            payment_objects=checkout_payment_blik_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="inpost_company",
            delivery_type=DeliveryTypes.INPOST,
            delivery_objects=private_person_delivery_inpost_receiver(),
            purchaser_objects=company_checkout_purchaser(),
            payment_objects=checkout_payment_blik_required_terms(),
        ),
        CheckoutDeliveryCase(
            case_id="store_pickup_company",
            delivery_type=DeliveryTypes.STORE_PICKUP,
            delivery_objects=private_person_delivery_storehouse_receiver(),
            purchaser_objects=company_checkout_purchaser(),
            payment_objects=checkout_payment_cash_on_pickup_required_terms(),
        ),
    ]
