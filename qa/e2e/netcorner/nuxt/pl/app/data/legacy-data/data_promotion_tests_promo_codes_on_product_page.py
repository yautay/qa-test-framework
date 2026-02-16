import copy

from TestData.CommonData.CommonData import CommonData
from TestData.CommonData.PromoCodeCommonData import common_test_promotion_codes
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    FilterSetKey,
    OrderAsKey,
    PaymentKey,
    PromotionCodeTypeKey,
    PurchaserKey,
    ReceiverKey,
)
from tools.InsertsGenerator.komputronik.lib.generators.products.products_data import (
    product_price_tests_products_ids,
)
from tools.InsertsGenerator.komputronik.lib.templates.promotions_promotion_service.promotions_dict import (
    promotions_data as fake_promotions_service_data,
)

scenario_promotion_code_on_product_page = (
    "Scenariusz:\n"
    "1. Testy opierają się na promocjach testowych zaimportowanych z bazy danych.\n"
    "2. Test otwiera kartę produktu i sprawdza widoczność kodu promocyjnego na karcie produktu.\n"
    "3. Produkt zostaje dodany do koszyka.\n"
    "4. W koszyku asercje odnoszą się do cen produktu oraz wartości promocji.\n"
    "5. Następnie składane jest zamówienie.\n"
    "6. W szczegółach zamówienia, zarówno na poziomie TYP, jak i w panelu administracyjnym sklepu, weryfikowane są "
    "ceny, promocje oraz koszty transportu."
)

scenario_promotion_code_on_product_page_exclusions = (
    "Scenariusz:\n"
    "1. Testy opierają się na promocjach testowych zaimportowanych z bazy danych.\n"
    "2. Test otwiera kartę produktu i sprawdza widoczność kodu promocyjnego na karcie produktu.\n"
    "3. Produkt zostaje dodany do koszyka.\n"
    "4. W koszyku asercje odnoszą się do cen produktu oraz wartości promocji.\n"
    "5. Następnie składane jest zamówienie.\n"
    "6. W szczegółach zamówienia, zarówno na poziomie TYP, jak i w panelu administracyjnym sklepu, weryfikowane są "
    "ceny, promocje oraz koszty transportu."
)

pl_var = PlCommonData.variables(test_storehouses=True)
categories = CommonData.key_categories()
common_test_data = {
    "register_data": PlCommonData.common_client(),
    "order_as": OrderAsKey.JUST_LOG_USER,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}

promotion_code_on_product_page = {"scenario": scenario_promotion_code_on_product_page,
                                  "test_product": int(product_price_tests_products_ids[12]),
                                  "promo_code": common_test_promotion_codes[PromotionCodeTypeKey.PUBLIC_A]["code"],
                                  "promotion": fake_promotions_service_data[14]}

promotion_code_on_product_page.update(copy.deepcopy(common_test_data))

promotion_code_on_product_page_exclusions_single_producer = {
    "scenario": scenario_promotion_code_on_product_page_exclusions,
    "category": categories["headphones"],
    "promo_code": common_test_promotion_codes[PromotionCodeTypeKey.PUBLIC_B]["code"],
    "filters": {"exclude": PlCommonData.filters()[FilterSetKey.PHILIPS]},
}

promotion_code_on_product_page_exclusions_producer_and_category = {
    "scenario": scenario_promotion_code_on_product_page_exclusions,
    "category": categories["smartwatches"],
    "promo_code": common_test_promotion_codes[PromotionCodeTypeKey.PUBLIC_C]["code"],
    "filters": {"exclude": PlCommonData.filters()[FilterSetKey.SUUNTO]}
}
