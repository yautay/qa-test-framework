from TestData.CommonData.PromoCodeCommonData import common_test_promotion_codes
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PromotionCodeTypeKey,
    PurchaserKey,
    ReceiverKey,
)
from tools.InsertsGenerator.komputronik.lib.templates.promotions_promotion_service.promotions_dict import (
    promotions_data as fake_promotions_service_data,
)

scenario_promo_code_aggregator = "Scenariusz: \n" \
                       "   1. Wchodzi na stronę serwisu promocji i tworzy nową promocję typu 'KOD PROMOCYJNY'.\n" \
                       "   2. Wchodzi na stronę admin NC i tworzy nowy kod promocyjny łącząc go z ww. promocją.\n" \
                       "   3. Tworzy agregator, dodaje do agregatora produkt z kodem promocyjnym.\n" \
                       "   4. Sprawdza czy promocja nalicza się poprawnie.\n" \
                       "   5. Składa zamówienie z produktem z agregatora.\n"

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "register_data": PlCommonData.register_data(),
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}

promo_code_aggregator = {
    "aggregator_data": PlCommonData.aggregator_data_products(),
    "aggregator_element_data": PlCommonData.aggregator_products_element_data(),
    "promotion": fake_promotions_service_data[5],
    "type": PromotionCodeTypeKey.AGGREGATOR,
    "code": common_test_promotion_codes[PromotionCodeTypeKey.AGGREGATOR]["code"]
}

promo_code_aggregator.setdefault("scenario", scenario_promo_code_aggregator)
promo_code_aggregator.update(common_test_data.copy())
