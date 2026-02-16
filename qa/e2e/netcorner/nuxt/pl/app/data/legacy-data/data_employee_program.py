from copy import deepcopy

from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_create_QR = "Scenariusz: \n" \
                     "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                     "   2. Tworzy grupę partnerów z opcją kod QR"
scenario_create_SMS = "Scenariusz: \n" \
                      "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                      "   2. Tworzy grupę partnerów z opcją kod SMS.\n" \
                      "   3. Weryfikuje unikalność tokenów SMS."
scenario_edit_QR = "Scenariusz: \n" \
                   "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                   "   2. Edytuje grupę partnerów z opcją kod QR tworząc nowy kod QR"
scenario_delete_group = "Scenariusz: \n" \
                        "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                        "   2. Usuwa grupę partnerów"
scenario_login_QR = "Scenariusz: \n" \
                    "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                    "   2. Tworzy grupę partnerów z opcją kod QR.\n" \
                    "   3. Loguje użytkowinika za pomocą kodu QR.\n" \
                    "   4. Weryfikuje czy użytkownik jest zarejestrowany w grupie partnerów."
scenario_register_QR = "Scenariusz: \n" \
                       "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                       "   2. Tworzy grupę partnerów z opcją kod QR.\n" \
                       "   3. Rejestruje użytkowinika za pomocą kodu QR.\n" \
                       "   4. Weryfikuje czy użytkownik jest zarejestrowany w grupie partnerów."
scenario_login_SMS = "Scenariusz: \n" \
                     "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                     "   2. Tworzy grupę partnerów z opcją kod SMS.\n" \
                     "   3. Loguje użytkowinika za pomocą kodu SMS.\n" \
                     "   4. Weryfikuje czy użytkownik jest zarejestrowany w grupie partnerów."
scenario_register_SMS = "Scenariusz: \n" \
                        "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                        "   2. Tworzy grupę partnerów z opcją kod SMS.\n" \
                        "   3. Rejestruje użytkowinika za pomocą kodu SMS.\n" \
                        "   4. Weryfikuje czy użytkownik jest zarejestrowany w grupie partnerów."
scenario_order_employee_program_QR = "Scenariusz: \n" \
                                     "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                                     "   2. Tworzy grupę partnerów z opcją kod QR.\n" \
                                     "   3. Loguje użytkowinika za pomocą kodu QR.\n" \
                                     "   4. Składa zamówienie.\n" \
                                     "   5. Weryfikuje czy zamówienie posiada odpowiednią kat. cenową."

scenario_order_employee_program_SMS = "Scenariusz: \n" \
                                      "   1. Grupy pracowników firm > Lista grup /admin.php/partnerEmployeeGroup/list/pl.\n" \
                                      "   2. Tworzy grupę partnerów z opcją kod SMS.\n" \
                                      "   3. Loguje użytkowinika za pomocą kodu SMS.\n" \
                                      "   4. Składa zamówienie.\n" \
                                      "   5. Weryfikuje czy zamówienie posiada odpowiednią kat. cenową."

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART,
    "category": CommonData.key_categories()["router"],
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}

common_sms_test_data = {
    "client_email": "sklep@komputronik.pl",
    "subject": "Link dla pracownika partnera"
}

data_create_employee_program_QR = {
    "scenario": scenario_create_QR,
    "group_config": PlCommonData.default_partner_group_qr(),
}

data_edit_employee_program_QR = {
    "scenario": scenario_edit_QR,
    "group_config": PlCommonData.default_partner_group_qr(),
}

data_delete_employee_program_QR = {
    "scenario": scenario_delete_group,
    "group_config": PlCommonData.default_partner_group_qr(),
}

data_create_employee_program_SMS = {
    "scenario": scenario_create_SMS,
    "group_config": PlCommonData.default_partner_group_sms(),
    "sms_test_data": common_sms_test_data,
}

data_delete_employee_program_SMS = {
    "scenario": scenario_delete_group,
    "group_config": PlCommonData.default_partner_group_sms(),
    "sms_test_data": common_sms_test_data,
}

data_login_employee_program_QR = {
    "scenario": scenario_login_QR,
    "register_data": PlCommonData.register_data(),
    "group_config": PlCommonData.default_partner_group_qr(),
}
data_login_employee_program_QR.update(deepcopy(common_test_data))

data_register_employee_program_QR = {
    "scenario": scenario_register_QR,
    "register_data": PlCommonData.register_data(),
    "group_config": PlCommonData.default_partner_group_qr(),
}
data_register_employee_program_QR.update(deepcopy(common_test_data))

data_login_employee_program_SMS = {
    "scenario": scenario_login_SMS,
    "register_data": PlCommonData.register_data(),
    "group_config": PlCommonData.default_partner_group_sms(),
    "sms_test_data": common_sms_test_data,
}
data_login_employee_program_SMS.update(deepcopy(common_test_data))

data_register_employee_program_SMS = {
    "scenario": scenario_register_SMS,
    "register_data": PlCommonData.register_data(),
    "group_config": PlCommonData.default_partner_group_sms(),
    "sms_test_data": common_sms_test_data,
}
data_register_employee_program_SMS.update(deepcopy(common_test_data))

data_order_employee_program_QR = {
    "scenario": scenario_order_employee_program_QR,
    "register_data": PlCommonData.register_data(),
    "group_config": PlCommonData.default_partner_group_qr()}
data_order_employee_program_QR.update(deepcopy(common_test_data))

data_order_employee_program_SMS = {
    "scenario": scenario_order_employee_program_SMS,
    "register_data": PlCommonData.register_data(),
    "group_config": PlCommonData.default_partner_group_sms()}
data_order_employee_program_SMS.update(deepcopy(common_test_data))
