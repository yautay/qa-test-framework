from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
)

scenario = "Scenariusz: \n" \
           "   1. Otwiera stronę z produktem i dodaje produkt do koszyka.\n" \
           "   2. W koszyku wybiera zamów z odbiorem własnym.\n" \
           "   3. Klika w przycisk 'DHL POP'.\n" \
           "   4. Wpisuje lokalizacje i wybiera punkt.\n" \
           "   5. Składa zamówienie z danymi dla odbiorcy i typem płatności."

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "register_data": PlCommonData.register_data(),
    "category": CommonData.url_product_list()["keyboards"],
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "delivery_location": PlCommonData.cart_variables()["delivery_location_postal_60001"],
                        "delivery_point_name": PlCommonData.cart_variables(
                            test_storehouses=True)["delivery_point_name_poznan_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}

dhlpop_non_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED.value,
}

dhlpop_registered = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED.value
}

dhlpop_registered.update(common_test_data.copy())
dhlpop_non_registered.update(common_test_data.copy())

dhlpop_non_registered.setdefault("scenario", scenario)
dhlpop_registered.setdefault("scenario", scenario)
