

scenario_omnibus_prices = {
        "Scenariusz:\n"
        "   1. Otwiera kartę produktu.\n"
        "   2. Weryfikuje ceny produktów testowych zgodnie z rozpiską w conflu.\n"
}

data_omnibus_A = {
    "scenario": scenario_omnibus_prices,
    "product_id": "500000501",
    "expected_final_price": 100,
    "expected_base_price": 130,
    "expected_omnibus_price": 110,
}
data_omnibus_B = {
    "scenario": scenario_omnibus_prices,
    "product_id": "500000502",
    "expected_final_price": 100,
    "expected_base_price": None,
    "expected_omnibus_price": None,
}
data_omnibus_C = {
    "scenario": scenario_omnibus_prices,
    "product_id": "500000503",
    "expected_final_price": 100,
    "expected_base_price": None,
    "expected_omnibus_price": None,
}
data_omnibus_D = {
    "scenario": scenario_omnibus_prices,
    "product_id": "500000504",
    "expected_final_price": 100,
    "expected_base_price": 130,
    "expected_omnibus_price": 140,
}
data_omnibus_E = {
    "scenario": scenario_omnibus_prices,
    "product_id": "500000505",
    "expected_final_price": 100,
    "expected_base_price": None,
    "expected_omnibus_price": None,
    "expected_outlet_price": 130
}
