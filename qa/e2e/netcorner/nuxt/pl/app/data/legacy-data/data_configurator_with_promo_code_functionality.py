from TestData.CommonData.PromoCodeCommonData import common_test_promotion_codes
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    ButtonNameKey,
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

scenario_promo_code_minimal_mandatory_and_3_optional_components_as_set = "Scenariusz: \n" \
                                       "   1. Przechodzi do panelu admina i sprawdza czy kod rabatowy jest dodany. Jeżeli nie to dodaje.\n" \
                                       "   2. Przechodzi na stronę konfiguratora PC.\n" \
                                       "   3. Dodaje do koszyka produkty ze statusem " \
                                       "'Wysyłamy najczęściej w 1 dzień roboczy'.\n" \
                                       "   4. Sekcja z błędami jest widoczna.\n" \
                                       "   5. Sprawdza aktywność przycisku 'Zamów jako części'.\n" \
                                       "   6. Klika w przycisk: Zamów jako części i dodaje kod rabatowy.\n" \
                                       "   7. Składa zamówienie z przesyłką kurierską z danymi odbiorcy" \
                                       " i płatnością.\n" \
                                       "   8. Czeka na pojawienie się thank you page."

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

promo_code_minimal_mandatory_and_3_optional_components_as_set = {
    "components_list": pl_var["components_set"],
    "components_optional": pl_var["components_optional"],
    "error_section_visible": True,
    "active_buttons": ButtonNameKey.PARTS,
    "button_order_as": ButtonNameKey.PARTS,
    "pc_montage": False,
    "promotion": fake_promotions_service_data[4],
    "type": PromotionCodeTypeKey.CONFIGURATOR,
    "code": common_test_promotion_codes[PromotionCodeTypeKey.CONFIGURATOR]["code"]
}

promo_code_minimal_mandatory_and_3_optional_components_as_set.setdefault(
    "scenario", scenario_promo_code_minimal_mandatory_and_3_optional_components_as_set)
promo_code_minimal_mandatory_and_3_optional_components_as_set.update(common_test_data.copy())
