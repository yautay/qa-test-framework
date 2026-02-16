from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PurchaserKey,
    ReceiverKey,
)

pl_var = PlCommonData.variables()
pl_var_forms = PlCommonData.forms_common_data_set()

scenario = "Scenariusz: \n"\
            "   1. Rejestruje nowego klienta.\n"\
            "   2. Wchodzi na stronę zarządzania kontem klienta.\n"\
            "   3. Wypełnia formularze nabywcy/odbiorcy.\n"\
            "   4. Waliduje formularze"

common_test_data = {
    "scenario": scenario,
    "register_data": PlCommonData.register_data(),
    "order_as": OrderAsKey.ORDER_AS_REGISTERED
}
common_forms_data = {
    "form_data": [
        pl_var_forms["forms_empty_form"],
        pl_var_forms["forms_one_character"],
        pl_var_forms["forms_special_characters"],
        pl_var_forms["forms_numeric_characters"],
        pl_var_forms["forms_alfa_numeric_characters"],
        pl_var_forms["forms_wrong_phone_number"],
    ],
    "form_errors": [
        pl_var_forms["forms_empty_form_expected_errors"],
        pl_var_forms["forms_one_character_expected_errors"],
        pl_var_forms["forms_special_characters_expected_errors"],
        pl_var_forms["forms_numeric_characters_expected_errors"],
        pl_var_forms["forms_alfa_numeric_characters_expected_errors"],
        pl_var_forms["forms_wrong_phone_number_expected_errors"],
    ]
}

private_receiver_fill_form = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_type": ReceiverKey.PRIVATE,
                        "receiver_data": common_forms_data["form_data"],
                        "receiver_data_errors": common_forms_data["form_errors"]}
}
company_receiver_fill_form = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_type": ReceiverKey.COMPANY,
                        "receiver_data": common_forms_data["form_data"],
                        "receiver_data_errors": common_forms_data["form_errors"]}
}

private_purchaser_fill_form = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_type": PurchaserKey.PRIVATE,
                         "purchaser_data": common_forms_data["form_data"],
                         "purchaser_data_errors": common_forms_data["form_errors"]}
}
company_purchaser_fill_form = {
    "purchaser_object": {"order_as": PurchaserKey.COMPANY,
                         "purchaser_type": PurchaserKey.COMPANY,
                         "purchaser_data": common_forms_data["form_data"],
                         "purchaser_data_errors": common_forms_data["form_errors"]}
}

private_receiver_fill_form.update(common_test_data.copy())
company_receiver_fill_form.update(common_test_data.copy())
private_purchaser_fill_form.update(common_test_data.copy())
company_purchaser_fill_form.update(common_test_data.copy())
