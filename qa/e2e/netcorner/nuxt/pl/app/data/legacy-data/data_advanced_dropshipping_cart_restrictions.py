from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    DropshippingProductKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_1 = "Scenariusz: \n" \
             "   1. Otwiera produkt DS i dodaje go do koszyka.\n" \
             "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny.\n" \
             "   3. Zwiększa ilość sztuk w koszyku do 4. \n" \
             "   4. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny \n" \
             "   5. Zwiększa ilość sztuk w koszyku do 5. \n" \
             "   6. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny \n"

scenario_2 = "Scenariusz: \n" \
             "   1. Otwiera produkt DS i dodaje go do koszyka.\n" \
             "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny.\n" \
             "   3. Zwiększa ilość sztuk w koszyku do 2. \n" \
             "   4. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny \n"

scenario_3 = "Scenariusz: \n" \
             "   1. Otwiera produkt DS i dodaje do koszyka.\n" \
             "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny.\n" \
             "   3. Zwiększa ilość sztuk w koszyku do 2. \n" \
             "   4. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny \n"

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_var = PlCommonData.variables()
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()
pl_ds_products = PlCommonData.dropshipping_products()

product_advanced_1 = {
    "product_code": pl_ds_products[DropshippingProductKey.DROPSHIPPING_ADV_1],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "methods_allowed": pl_cart_rest_var["dropshipping"]},
}
product_advanced_2 = {
    "product_code": pl_ds_products[DropshippingProductKey.DROPSHIPPING_ADV_2],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_dhlpop"]},
}
product_advanced_3 = {
    "product_code": [pl_ds_products[DropshippingProductKey.DROPSHIPPING_ADV_3],
                     pl_ds_products[DropshippingProductKey.DROPSHIPPING_ADV_4]],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "receiver_data": PlCommonData.receiver_data(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}

product_advanced_1.setdefault("scenario", scenario_1)
product_advanced_2.setdefault("scenario", scenario_2)
product_advanced_3.setdefault("scenario", scenario_3)
