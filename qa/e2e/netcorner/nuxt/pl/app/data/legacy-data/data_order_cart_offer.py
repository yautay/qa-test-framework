from TestCases.NetCornerProducts.Common.DictKeys.CartOfferKeys import CartOfferKeys
from TestData.CommonData.SalesChannels import SalesChannels
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)
from tools.InsertsGenerator.komputronik.lib.generators.products.products_data import (
    product_price_tests_products_ids,
)

scenario = "Scenariusz: \n" \
           "   1. Tworzy ofertę koszykową.\n" \
           "   2. Z poziomu oferty dodaje produkt do koszyka.\n" \
           "   3. Przechodzi na stronę szczegółami zamówienia (uzytkownik i admin)." \
           "   4. Sprawdza czy ceny są zgodne z oczekiwanymi.\n"

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "scenario": scenario,
    "order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART,
    "register_data": PlCommonData.register_data(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
data_order_cart_offer_static = {
    "cart_offer": {CartOfferKeys.CHANNEL: SalesChannels.KOMPUTRONIK,
                   CartOfferKeys.PRODUCTS: [{CartOfferKeys.PRODUCT_ID: product_price_tests_products_ids[1],
                                             CartOfferKeys.PRODUCT_QTY: 3, CartOfferKeys.PRODUCT_PRICE: 119}]}

}
data_order_cart_offer_dynamic = {
    "cart_offer": {CartOfferKeys.CHANNEL: SalesChannels.KOMPUTRONIK,
                   CartOfferKeys.PRODUCTS: [{CartOfferKeys.PRODUCT_ID: product_price_tests_products_ids[1],
                                             CartOfferKeys.PRODUCT_QTY: 3}]}

}
data_order_cart_offer_static.update(common_test_data.copy())
data_order_cart_offer_dynamic.update(common_test_data.copy())
