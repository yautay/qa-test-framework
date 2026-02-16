import copy

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
           "   2. W koszyku wybiera zamów z odbiorem w salonie.\n" \
           "   3. Z listy salonów wybiera salon partnerski.\n" \
           "   4. Składa zamówienie z danymi dla odbiorcy i typem płatności.\n" \
           "   5. W MAILHOG weryfikuje korespondencję e-mail"

pl_var = PlCommonData.variables(test_storehouses=True)
common_test_data = {
    "category": CommonData.url_product_list()["keyboards"],
    "register_data": PlCommonData.common_client(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "delivery_location": pl_var["delivery_point_partner_storehouse"],
                        "delivery_point_name": pl_var["delivery_point_partner_storehouse"]},
    "payment_option": PaymentKey.CASH

}

partner_storehouse_non_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED.value
}

partner_storehouse_registered = {
    "order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART.value
}

partner_storehouse_registered.update(copy.deepcopy(common_test_data))
partner_storehouse_non_registered.update(copy.deepcopy(common_test_data))

partner_storehouse_non_registered.setdefault("scenario", scenario)
partner_storehouse_registered.setdefault("scenario", scenario)
