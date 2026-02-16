import copy

from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

from settings import email_for_production_tests

scenario_common = "Scenariusz: \n" \
                  "   1. {}\n" \
                  "   2. Czeka 60 sek. na wybór i manualne dodanie produktu do koszyka przez testera.\n" \
                  "   3. Automat kontynuuje proces zakupowy\n" \
                  "   4. Składa zamówienie i czeka na pojawienie się thank you page."

login_test_client = "Otwiera stronę główną oraz loguje testowego klienta"
register_test_client = "Otwiera stronę główną oraz rejestruje testowego klienta"

overwritten_data_register = PlCommonData.register_data()
overwritten_data_register["email"] = email_for_production_tests

overwritten_data_receiver = PlCommonData.receiver_data_ktpl()
overwritten_data_receiver["mail"] = email_for_production_tests

overwritten_data_purchaser = PlCommonData.purchaser_data_ktpl()
overwritten_data_purchaser["mail"] = email_for_production_tests

pl_var = PlCommonData.variables()

common_test_data = {
    "scenario": scenario_common.format(login_test_client),
    "register_data": PlCommonData.common_client(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "comment_to_order": "Zamówienie testowe PiRO, proszę o anulowanie."
}

courier_common_data = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE
                        },
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER}

pickup_common_data = {
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "delivery_location": pl_var["delivery_city_poznan"],
                        "delivery_point_name": pl_var["delivery_point_poznan_plaza"]},
    "payment_option": PaymentKey.CASH}

delivery_at_home_registered_with_email_from_settings_data = {
    "scenario": scenario_common.format(register_test_client),
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
    "register_data": overwritten_data_register,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": overwritten_data_purchaser},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": overwritten_data_receiver,
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER}

delivery_at_home_logged_in_cart = {"order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART_SKIP_REGISTRATION}
delivery_at_home_non_registered = {"order_as": OrderAsKey.ORDER_AS_NON_REGISTERED}
self_pickup_registered = {"order_as": OrderAsKey.ORDER_AS_REGISTERED}
self_pickup_logged_in_cart = {"order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART_SKIP_REGISTRATION}
self_pickup_non_registered = {"order_as": OrderAsKey.ORDER_AS_NON_REGISTERED}

delivery_at_home_registered_with_email_from_settings = copy.deepcopy(common_test_data)
delivery_at_home_registered_with_email_from_settings.update(
    delivery_at_home_registered_with_email_from_settings_data)

courier_common_data.update(copy.deepcopy(common_test_data))
delivery_at_home_logged_in_cart.update(copy.deepcopy(courier_common_data))
delivery_at_home_non_registered.update(copy.deepcopy(courier_common_data))
pickup_common_data.update(copy.deepcopy(common_test_data))
self_pickup_registered.update(copy.deepcopy(pickup_common_data))
self_pickup_logged_in_cart.update(copy.deepcopy(pickup_common_data))
self_pickup_non_registered.update(copy.deepcopy(pickup_common_data))
