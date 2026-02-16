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
    fake_frontend_test_products_ids,
)
from tools.InsertsGenerator.komputronik.lib.templates.promotions_promotion_service.promotions_dict import (
    promotions_data as fake_promotions_service_data,
)
from tools.InsertsGenerator.komputronik.lib.templates.promotions_sezam.promotions_sezam_dict import (
    fake_sezam_promotions_data,
)

scenario_promotion_sezam = (
    "Scenariusz:\n"
    "1. Testy przekreślonych cen opierają się na promocjach testowych zaimportowanych z bazy danych.\n"
    "2. Test otwiera kartę produktu i sprawdza widoczność promocji w postaci przekreślonej ceny.\n"
    "3. Na karcie produktu asercje dotyczą zarówno ceny produktu, jak i wartości promocji.\n"
    "4. Produkt zostaje dodany do koszyka.\n"
    "5. W koszyku asercje odnoszą się do cen produktu oraz wartości promocji.\n"
    "6. Następnie składane jest zamówienie.\n"
    "7. W szczegółach zamówienia, zarówno na poziomie TYP, jak i w panelu administracyjnym sklepu, weryfikowane są "
    "ceny, promocje oraz koszty transportu."
)
scenario_promotion_service = (
    "Scenariusz:\n"
    "1. Testy przekreślonych cen opierają się na promocjach testowych zaimportowanych z bazy danych.\n"
    "2. Test otwiera kartę produktu i sprawdza widoczność promocji.\n"
    "3. Na karcie produktu asercje dotyczą zarówno ceny produktu, jak i wartości promocji.\n"
    "4. Produkt zostaje dodany do koszyka.\n"
    "5. W koszyku asercje odnoszą się do cen produktu oraz wartości promocji.\n"
    "6. Następnie składane jest zamówienie.\n"
    "7. W szczegółach zamówienia, zarówno na poziomie TYP, jak i w panelu administracyjnym sklepu, weryfikowane są "
    "ceny, promocje oraz koszty transportu."
)
scenario_promotion_codes = (
    "Scenariusz:\n"
    "1. Testy kodów promocyjnych bazują na kodach testowych zaimportowanych z bazy danych.\n"
    "2. Testy weryfikują działanie kodów typu przedpłata, afiliacja oraz promocja\n"
    "3. Test weryfikuje proces zakupowy z wykorzystaniem ww. kodów.\n"
    "4. Produkt zostaje dodany do koszyka.\n"
    "5. W szczegółach zamówienia w panelu administracyjnym sklepu, weryfikowane jest działanie kodów."
)
scenario_promotion_visibility = (
    "Scenariusz:\n"
    "1. Testy bazują na promocjach testowych zaimportowanych z bazy danych.\n"
    "2. Testy weryfikują widoczność promocji zgodnie z konfiguracją\n"
)
pl_var = PlCommonData.variables(test_storehouses=True)
categories = CommonData.key_categories()

common_test_data = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER}

promotion_sezam_percent = {"scenario": scenario_promotion_sezam,
                           "promotion": {"promotion_test_id": 1,
                                         "promotion_db_id": fake_sezam_promotions_data[1]["promotion_id"]},
                           "test_product": fake_frontend_test_products_ids[
                               fake_sezam_promotions_data[1]["products_mapper"][1]]}
promotion_sezam_value = {"scenario": scenario_promotion_sezam,
                         "promotion": {"promotion_test_id": 6,
                                       "promotion_db_id": fake_sezam_promotions_data[6]["promotion_id"]},
                         "test_product": fake_frontend_test_products_ids[
                             fake_sezam_promotions_data[6]["products_mapper"][1]]}
promotion_sezam_fixed = {"scenario": scenario_promotion_sezam,
                         "promotion": {"promotion_test_id": 11,
                                       "promotion_db_id": fake_sezam_promotions_data[11]["promotion_id"]},
                         "test_product": fake_frontend_test_products_ids[
                             fake_sezam_promotions_data[11]["products_mapper"][1]]}
promotion_sezam_percent.update(copy.deepcopy(common_test_data))
promotion_sezam_value.update(copy.deepcopy(common_test_data))
promotion_sezam_fixed.update(copy.deepcopy(common_test_data))

promotion_standard_discount = {"scenario": scenario_promotion_service,
                               "promotion": fake_promotions_service_data[1],
                               "with_lift": False}
promotion_free_shipping_big_size = {"scenario": scenario_promotion_service,
                                    "promotion": fake_promotions_service_data[2],
                                    "with_lift": True}
promotion_standard_discount.update(copy.deepcopy(common_test_data))
promotion_free_shipping_big_size.update(copy.deepcopy(common_test_data))

promo_code_promotion = {"scenario": scenario_promotion_codes,
                        "type": PromotionCodeTypeKey.PROMOTION,
                        "promotion": fake_promotions_service_data[1],
                        "code": common_test_promotion_codes[PromotionCodeTypeKey.PROMOTION]["code"]}
promo_code_prepaid = {"scenario": scenario_promotion_codes,
                      "type": PromotionCodeTypeKey.PREPAID,
                      "code": common_test_promotion_codes[PromotionCodeTypeKey.PREPAID]["code"]}
promo_code_affiliate = {"scenario": scenario_promotion_codes,
                        "type": PromotionCodeTypeKey.AFFILIATE,
                        "code": common_test_promotion_codes[PromotionCodeTypeKey.AFFILIATE]["code"],
                        "program": common_test_promotion_codes[PromotionCodeTypeKey.AFFILIATE]["program"]}

promo_code_promotion.update(copy.deepcopy(common_test_data))
promo_code_prepaid.update(copy.deepcopy(common_test_data))
promo_code_affiliate.update(copy.deepcopy(common_test_data))

promotion_visibility_producer_excluded = {
    "scenario": scenario_promotion_visibility,
    "category": categories["cpu"],
    "promotion": fake_promotions_service_data[16],
    "filters": {"exclude": PlCommonData.filters()[FilterSetKey.AMD],
                "include": PlCommonData.filters()[FilterSetKey.INTEL]},
}

promotion_producer_and_category_complex_case_cpu_intel_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["cpu"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.INTEL]
    }
promotion_producer_and_category_complex_case_cpu_amd_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["cpu"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.AMD]
    }
promotion_producer_and_category_complex_case_ram_kingston_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["ram"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.KINGSTON]
    }
promotion_producer_and_category_complex_case_hdd_samsung_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["int_hdd"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.SAMSUNG]
    }
promotion_producer_and_category_complex_case_gpu_intel_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["gpu"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.INTEL]
    }
promotion_producer_and_category_complex_case_mainboards_msi_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["mainboards"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.MSI]
    }

promotion_producer_and_category_complex_case_gpu_msi_not_visible = {
    "scenario": scenario_promotion_visibility,
    "category": categories["gpu"],
    "promotion": fake_promotions_service_data[17],
    "filters": PlCommonData.filters()[FilterSetKey.MSI]
    }
