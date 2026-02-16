from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
)

scenario = "Scenariusz: \n" \
           "   1. Otwiera stronę z produktem i dodaje produkt do koszyka.\n" \
           "   2. W koszyku wybiera zamów z odbiorem własnym.\n" \
           "   3. Klika w przycisk 'InPost'.\n" \
           "   4. Wpisuje lokalizacje i wybiera punkt odbioru.\n" \
           "   5. Składa zamówienie z danymi dla odbiorcy i typem płatności."

pl_var = PlCommonData.variables(test_storehouses=True)

inpost_non_registered = {
    "category": CommonData.url_product_list()["keyboards"],
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "delivery_location": PlCommonData.cart_variables()["delivery_location_postal_60001"],
                        "delivery_point_name": PlCommonData.cart_variables(
                            test_storehouses=True)["delivery_point_name_poznan_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
inpost_non_registered.setdefault("scenario", scenario)

