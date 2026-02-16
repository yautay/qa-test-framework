import copy

from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_purchaser_private = "Scenariusz: \n" \
                             "   1. Rejestruje klienta.\n" \
                             "   2. Wchodzi na stronę dodawania nabywcy.\n" \
                             "   3. Wypełnia formularz dla osoby prywatnej.\n" \
                             "   4. Zapisuje dane i sprawdza poprawność.\n" \
                             "   5. Klika w przycisk edycji i wprowadza dane.\n" \
                             "   6. Zapisuje dane i sprawdza poprawność.\n" \
                             "   7. Usuwa dane i sprawdza czy zostały usunięte."

scenario_purchaser_company = "Scenariusz: \n" \
                             "   1. Rejestruje klienta.\n" \
                             "   2. Wchodzi na stronę dodawania nabywcy.\n" \
                             "   3. Wypełnia formularz dla firmy.\n" \
                             "   4. Zapisuje dane i sprawdza poprawność.\n" \
                             "   5. Klika w przycisk edycji i wprowadza dane.\n" \
                             "   6. Zapisuje dane i sprawdza poprawność.\n" \
                             "   7. Usuwa dane i sprawdza czy zostały usunięte."

scenario_receiver_private = "Scenariusz: \n" \
                            "   1. Rejestruje klienta.\n" \
                            "   2. Wchodzi na stronę dodawania nabywcy.\n" \
                            "   3. Wypełnia formularz dla osoby prywatnej.\n" \
                            "   4. Zapisuje dane i sprawdza poprawność.\n" \
                            "   5. Klika w przycisk edycji i wprowadza dane.\n" \
                            "   6. Zapisuje dane i sprawdza poprawność.\n" \
                            "   7. Usuwa dane i sprawdza czy zostały usunięte."

scenario_receiver_company = "Scenariusz: \n" \
                            "   1. Rejestruje klienta.\n" \
                            "   2. Wchodzi na stronę dodawania nabywcy.\n" \
                            "   3. Wypełnia formularz dla firmy.\n" \
                            "   4. Zapisuje dane i sprawdza poprawność.\n" \
                            "   5. Klika w przycisk edycji i wprowadza dane.\n" \
                            "   6. Zapisuje dane i sprawdza poprawność.\n" \
                            "   7. Usuwa dane i sprawdza czy zostały usunięte."

common_var = CommonData()
common_test_data = {
    "category": common_var.url_product_list()["mice"],
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
    "register_data": PlCommonData.register_data(),
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
}

private_purchaser = copy.deepcopy(common_test_data)
private_purchaser["purchaser_object"] = {"order_as": PurchaserKey.PRIVATE,
                                         "purchaser_data": PlCommonData.purchaser_data_ktpl()}
edited_private_purchaser_data = copy.deepcopy(private_purchaser["purchaser_object"])
edited_private_purchaser_data["purchaser_data"]["name"] = "Adam"
edited_private_purchaser_data["purchaser_data"]["surname"] = "Edytowany"
private_purchaser["purchaser_object_edited"] = edited_private_purchaser_data
private_purchaser.setdefault("scenario", scenario_purchaser_private)

company_purchaser = copy.deepcopy(common_test_data)
company_purchaser["purchaser_object"] = {"order_as": PurchaserKey.COMPANY,
                                         "purchaser_data": PlCommonData.purchaser_data_non_gus()}
edited_company_purchaser_data = copy.deepcopy(company_purchaser["purchaser_object"])
edited_company_purchaser_data["purchaser_data"]["company"] = "Janusz Kompany Inc."
company_purchaser["purchaser_object_edited"] = edited_company_purchaser_data
company_purchaser.setdefault("scenario", scenario_purchaser_company)

company_purchaser_gus = copy.deepcopy(common_test_data.copy())
company_purchaser_gus["purchaser_object"] = {"order_as": PurchaserKey.COMPANY,
                                             "purchaser_data": PlCommonData.purchaser_data_gus()}
edited_company_purchaser_gus = copy.deepcopy(company_purchaser_gus["purchaser_object"])
edited_company_purchaser_gus["purchaser_data"]["mail"] = "tomatopasta@test.com"
company_purchaser_gus["purchaser_object_edited"] = edited_company_purchaser_gus
company_purchaser_gus.setdefault("scenario", scenario_purchaser_company)

private_receiver = copy.deepcopy(common_test_data.copy())
edited_private_receiver_data = copy.deepcopy(private_receiver["delivery_object"])
edited_private_receiver_data["receiver_data"]["name"] = "Adam"
edited_private_receiver_data["receiver_data"]["surname"] = "Edytowany"
private_receiver["delivery_object_edited"] = edited_private_receiver_data
private_receiver.setdefault("scenario", scenario_receiver_private)

company_receiver = copy.deepcopy(common_test_data.copy())
company_receiver["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
edited_company_receiver_data = copy.deepcopy(company_receiver["delivery_object"])
edited_company_receiver_data["receiver_data"]["company"] = "Janusz Kompany Inc."
company_receiver["delivery_object_edited"] = edited_company_receiver_data
company_receiver.setdefault("scenario", scenario_receiver_company)
