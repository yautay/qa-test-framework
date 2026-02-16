from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    ProductAvailabilityKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_adhoc_product_1 =                      "Scenariusz: \n" \
                                                "   1. Przejście na KP\n" \
                                                "   2. Weryfikacja kupowalności produktu - ma być kupowalny\n" \
                                                "   3. Kupuje produkt."
scenario_adhoc_product_2 =                      "Scenariusz: \n" \
                                                "   1. Przejście na KP\n" \
                                                "   2. Weryfikacja kupowalności produktu - ma być niekupowalny"
scenario_adhoc_product_3 =                      "Scenariusz: \n" \
                                                "   1. Przejście na KP\n" \
                                                "   2. Weryfikacja kupowalności produktu - ma być niekupowalny"
scenario_adhoc_product_4 =                      "Scenariusz: \n" \
                                                "   1. Przejście na KP\n" \
                                                "   2. Weryfikacja kupowalności produktu - ma być kupowalny\n" \
                                                "   3. Kupuje produkt."
common_test_data = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
data_adhoc_product_1 = {
    "scenario": scenario_adhoc_product_1,
    "product_id": 500001006,
    "expected_status": ProductAvailabilityKey.AVAILABLE_IN_2D.value
}
data_adhoc_product_1.update(common_test_data.copy())

data_adhoc_product_2 = {
    "scenario": scenario_adhoc_product_2,
    "product_id": 500001007,
    "expected_status": ProductAvailabilityKey.UNAVAILABLE.value
}

data_adhoc_product_3 = {
    "scenario": scenario_adhoc_product_3,
    "product_id": 500001008,
    "expected_status": ProductAvailabilityKey.UNAVAILABLE.value
}

data_adhoc_product_4 = {
    "scenario": scenario_adhoc_product_4,
    "product_id": 500001009,
    "expected_status": ProductAvailabilityKey.AVAILABLE.value
}
data_adhoc_product_4.update(common_test_data.copy())
