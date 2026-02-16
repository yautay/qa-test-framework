from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

pl_var = PlCommonData.variables()
pl_var_forms = PlCommonData.forms_common_data_set()

scenario = "Scenariusz: \n"\
           "   1. Dodaje produkt do koszyka i przechodzi na stronę procesu zakupowego z dostawą do domu.\n"\
           "   2. Wypełnia formularz odbiorcy i nabywcy i sprawdza oczekiwane błędy.\n"

common_test_data = {
    "scenario": scenario,
    "category": CommonData.url_product_list()["keyboards"],
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "order_status": pl_var["order_status_one_work_day"],
    "order_with": DeliveryMethodKey.COURIER,
    "payment_option": PaymentKey.BLIK,
}

common_forms_data = {
    "form_data_private": [
        pl_var_forms["forms_empty_form"],
        pl_var_forms["forms_one_character"],
        pl_var_forms["forms_special_characters"],
        pl_var_forms["forms_numeric_characters"],
        pl_var_forms["forms_alfa_numeric_characters"],
        pl_var_forms["forms_wrong_phone_number"],
        pl_var_forms["forms_correct_data_private"],
    ],
    "form_errors_private": [
        pl_var_forms["forms_empty_form_expected_errors"],
        pl_var_forms["forms_one_character_expected_errors"],
        pl_var_forms["forms_special_characters_expected_errors"],
        pl_var_forms["forms_numeric_characters_expected_errors"],
        pl_var_forms["forms_alfa_numeric_characters_expected_errors"],
        pl_var_forms["forms_wrong_phone_number_expected_errors"],
        pl_var_forms["forms_correct_data_private_expected_errors"],
    ],
    "form_data_company": [
        pl_var_forms["forms_empty_form"],
        pl_var_forms["forms_one_character"],
        pl_var_forms["forms_special_characters"],
        pl_var_forms["forms_numeric_characters"],
        pl_var_forms["forms_alfa_numeric_characters"],
        pl_var_forms["forms_wrong_phone_number"],
        pl_var_forms["forms_correct_data_company"],
    ],
    "form_errors_company": [
        pl_var_forms["forms_empty_form_expected_errors"],
        pl_var_forms["forms_one_character_expected_errors"],
        pl_var_forms["forms_special_characters_expected_errors"],
        pl_var_forms["forms_numeric_characters_expected_errors"],
        pl_var_forms["forms_alfa_numeric_characters_expected_errors"],
        pl_var_forms["forms_wrong_phone_number_expected_errors"],
        pl_var_forms["forms_correct_data_company_expected_errors"],
    ]
}

different_characters_private_receiver_purchaser = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_type": PurchaserKey.PRIVATE,
                         "purchaser_data": common_forms_data["form_data_private"],
                         "purchaser_data_errors": common_forms_data["form_errors_private"]},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_type": ReceiverKey.PRIVATE,
                        "receiver_data": common_forms_data["form_data_private"],
                        "receiver_data_errors": common_forms_data["form_errors_private"]}
}

different_characters_company_receiver_purchaser = {
    "purchaser_object": {"order_as": PurchaserKey.COMPANY,
                         "purchaser_type": PurchaserKey.COMPANY,
                         "purchaser_data": common_forms_data["form_data_company"],
                         "purchaser_data_errors": common_forms_data["form_errors_company"]},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_type": ReceiverKey.COMPANY,
                        "receiver_data": common_forms_data["form_data_private"],
                        "receiver_data_errors": common_forms_data["form_errors_private"]}
}

different_characters_private_receiver_purchaser.update(common_test_data.copy())
different_characters_company_receiver_purchaser.update(common_test_data.copy())
