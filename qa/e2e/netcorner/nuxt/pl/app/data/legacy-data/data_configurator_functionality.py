from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    ButtonNameKey,
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

from .PlCommonData import PlCommonData

scenario_minimal_components_as_parts = "Scenariusz: \n" \
                                       "   1. Otwiera stronę rejestracji i rejestruje klienta.\n" \
                                       "   2. Przechodzi na stronę konfiguratora.\n" \
                                       "   3. Dodaje do koszyka produkty ze statusem " \
                                       "'Wysyłamy najczęściej w 1 dzień roboczy'.\n" \
                                       "   4. Sekcja z błędami jest widoczna.\n" \
                                       "   5. Sprawdza aktywność przycisku 'Zamów jako części'.\n" \
                                       "   6. Klika w przycisk: Zamów jako części.\n" \
                                       "   7. Składa zamówienie z odbiorem osobistym w Poznań Outlet z danymi odbiorcy" \
                                       " i płatnością.\n" \
                                       "   8. Czeka na pojawienie się thank you page."

scenario_minimal_components_as_set = "Scenariusz: \n" \
                                     "   1. Otwiera stronę rejestracji i rejestruje klienta.\n" \
                                     "   2. Przechodzi na stronę konfiguratora.\n" \
                                     "   3. Dodaje do koszyka produkty ze statusem " \
                                     "'Wysyłamy najczęściej w 1 dzień roboczy'.\n" \
                                     "   4. Sekcja z błędami jest widoczna.\n" \
                                     "   5. Sprawdza aktywność obu przycisków.\n" \
                                     "   6. Klika w przycisk: Zamów jako zestaw.\n" \
                                     "   7. Składa zamówienie z odbiorem osobistym w Poznań Outlet z danymi odbiorcy" \
                                     " i płatnością.\n" \
                                     "   8. Czeka na pojawienie się thank you page."

scenario_all_as_set_with_montage = "Scenariusz: \n" \
                                   "   1. Otwiera stronę rejestracji i rejestruje klienta.\n" \
                                   "   2. Przechodzi na stronę konfiguratora.\n" \
                                   "   3. Dodaje do koszyka produkty ze statusem 'Wysyłamy najczęściej w 1 dzień" \
                                   " roboczy'.\n" \
                                   "   4. Sekcja z błędami nie jest widoczna.\n" \
                                   "   5. Sprawdza aktywność obu przycisków.\n" \
                                   "   6. Klika w przycisk: Zamów jako zestaw i wybiera montaż.\n" \
                                   "   7. Składa zamówienie z odbiorem osobistym w Poznań Outlet z danymi odbiorcy" \
                                   " i płatnością.\n" \
                                   "   8. Czeka na pojawienie się thank you page."

scenario_all_components_as_parts = "Scenariusz: \n" \
                                   "   1. Otwiera stronę rejestracji i rejestruje klienta.\n" \
                                   "   2. Przechodzi na stronę konfiguratora.\n" \
                                   "   3. Dodaje do koszyka produkty ze statusem 'Wysyłamy najczęściej w 1 dzień" \
                                   " roboczy'.\n" \
                                   "   4. Sekcja z błędami nie jest widoczna.\n" \
                                   "   5. Sprawdza aktywność obu przycisków.\n" \
                                   "   6. Klika w przycisk: Zamów jako części i nie wybiera montażu.\n" \
                                   "   7. Składa zamówienie z odbiorem osobistym w Poznań Outlet z danymi odbiorcy" \
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

minimal_mandatory_components = {
    "components_list": pl_var["components_minimal"],
    "error_section_visible": True,
    "active_buttons": ButtonNameKey.PARTS,
    "button_order_as": ButtonNameKey.PARTS,
    "pc_montage": False,
}
minimal_mandatory_components.setdefault("scenario", scenario_minimal_components_as_parts)
minimal_mandatory_components.update(common_test_data.copy())

all_mandatory_components_as_set_with_montage = {
    "components_list": pl_var["components_montage"],
    "error_section_visible": False,
    "active_buttons": ButtonNameKey.BOTH,
    "button_order_as": ButtonNameKey.SET,
    "pc_montage": True,
}
all_mandatory_components_as_set_with_montage.setdefault("scenario", scenario_all_as_set_with_montage)
all_mandatory_components_as_set_with_montage.update(common_test_data.copy())

all_mandatory_components_as_parts = {
    "components_list": pl_var["components_montage"],
    "error_section_visible": False,
    "active_buttons": ButtonNameKey.BOTH,
    "button_order_as": ButtonNameKey.PARTS,
    "pc_montage": False,
}
all_mandatory_components_as_parts.setdefault("scenario", scenario_all_components_as_parts)
all_mandatory_components_as_parts.update(common_test_data.copy())

minimal_mandatory_and_3_optional_components_as_set = {
    "components_list": pl_var["components_set"],
    "components_optional": pl_var["components_optional"],
    "error_section_visible": True,
    "active_buttons": ButtonNameKey.PARTS,
    "button_order_as": ButtonNameKey.PARTS,
    "pc_montage": False,
}
minimal_mandatory_and_3_optional_components_as_set.setdefault("scenario", scenario_minimal_components_as_set)
minimal_mandatory_and_3_optional_components_as_set.update(common_test_data.copy())

all_mandatory_and_3_optional_components_as_set_with_montage = {
    "components_list": pl_var["components_all"],
    "components_optional": pl_var["components_optional"],
    "error_section_visible": False,
    "active_buttons": ButtonNameKey.BOTH,
    "button_order_as": ButtonNameKey.SET,
    "pc_montage": True,
}
all_mandatory_and_3_optional_components_as_set_with_montage.setdefault(
    "scenario", scenario_all_as_set_with_montage)
all_mandatory_and_3_optional_components_as_set_with_montage.update(common_test_data.copy())
