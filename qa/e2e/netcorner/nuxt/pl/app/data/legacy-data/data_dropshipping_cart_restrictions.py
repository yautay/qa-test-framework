from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    DropshippingProductKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Weryfikuje dostępne metody transportu.\n"

scenario2 = "Scenariusz: \n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny.\n" \
            "   3. Zwiększa ilość produktów do 2 i weryfikuje czy przycisk 'Przejdź dalej' nie jest aktywny"

scenario3 = "Scenariusz: \n" \
            "   1. Otwiera odpowiednie produkty i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Weryfikuje dostępne metody transportu.\n"

scenario4 = "Scenariusz: \n" \
            "   1. Otwiera odpowiednie produkty i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Zwiększa ilość poszczególnych produktów do 2 i weryfikuje czy przycisk 'Przejdź dalej' nie jest" \
            " aktywny"

scenario5 = "Scenariusz: \n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Wybiera wysyłkę kurierem.\n" \
            "   4. Uzupełnia wszystkie dane i sprawdza czy na pewno nie pojawila sie macierz, składa zamówienie.\n"

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_var = PlCommonData.variables()
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()
pl_ds_products = PlCommonData.dropshipping_products()

product_dropshipper = {
    "product_code": pl_ds_products[DropshippingProductKey.DROPSHIPPING],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["dropshipping"]},
    "availability_status": pl_var["order_status_dropshipping"]
}
product_supplier = {
    "product_code": pl_ds_products[DropshippingProductKey.SUPPLIER],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "availability_status": pl_var["order_status_3_to_5_days"]
}
product_due_supply = {
    "product_code": pl_ds_products[DropshippingProductKey.DUE_SUPLY],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "availability_status": pl_var["order_status_due_delivery"]
}

product_dropshipper.setdefault("scenario", scenario1)
product_supplier.setdefault("scenario", scenario1)
product_due_supply.setdefault("scenario", scenario1)

product_dropshipper_increase = product_dropshipper.copy()
product_supplier_increase = product_supplier.copy()
product_due_supply_increase = product_due_supply.copy()

product_dropshipper_increase.setdefault("scenario", scenario2)
product_supplier_increase.setdefault("scenario", scenario2)
product_due_supply_increase.setdefault("scenario", scenario2)

cross_products_active_ds_sup = product_supplier.copy()
cross_products_active_ds_dus = product_supplier.copy()
cross_products_active_sup_dus = product_supplier.copy()
cross_products_active_ds_sup_dus = product_supplier.copy()

cross_products_active_ds_sup["product_code"] = [pl_ds_products[DropshippingProductKey.DROPSHIPPING],
                                                pl_ds_products[DropshippingProductKey.SUPPLIER]]
cross_products_active_ds_dus["product_code"] = [pl_ds_products[DropshippingProductKey.DROPSHIPPING],
                                                pl_ds_products[DropshippingProductKey.DUE_SUPLY]]
cross_products_active_sup_dus["product_code"] = [pl_ds_products[DropshippingProductKey.SUPPLIER],
                                                 pl_ds_products[DropshippingProductKey.DUE_SUPLY]]
cross_products_active_ds_sup_dus["product_code"] = [pl_ds_products[DropshippingProductKey.DROPSHIPPING],
                                                    pl_ds_products[DropshippingProductKey.SUPPLIER],
                                                    pl_ds_products[DropshippingProductKey.DUE_SUPLY]]
cross_products_active_ds_sup["availability_status"] = [pl_var["order_status_dropshipping"],
                                                       pl_var["order_status_3_to_5_days"]]
cross_products_active_ds_dus["availability_status"] = [pl_var["order_status_dropshipping"],
                                                       pl_var["order_status_due_delivery"]]
cross_products_active_sup_dus["availability_status"] = [pl_var["order_status_3_to_5_days"],
                                                        pl_var["order_status_due_delivery"]]
cross_products_active_ds_sup_dus["availability_status"] = [pl_var["order_status_dropshipping"],
                                                           pl_var["order_status_3_to_5_days"],
                                                           pl_var["order_status_due_delivery"]]

cross_products_active_ds_sup.setdefault("scenario", scenario3)
cross_products_active_ds_dus.setdefault("scenario", scenario3)
cross_products_active_sup_dus.setdefault("scenario", scenario3)
cross_products_active_ds_sup_dus.setdefault("scenario", scenario3)

cross_products_active_ds_sup_inactive = cross_products_active_ds_sup.copy()
cross_products_active_ds_dus_inactive = cross_products_active_ds_dus.copy()
cross_products_active_sup_dus_inactive = cross_products_active_sup_dus.copy()
cross_products_active_ds_sup_dus_inactive = cross_products_active_ds_sup_dus.copy()

cross_products_active_ds_sup_inactive.setdefault("scenario", scenario4)
cross_products_active_ds_dus_inactive.setdefault("scenario", scenario4)
cross_products_active_sup_dus_inactive.setdefault("scenario", scenario4)
cross_products_active_ds_sup_dus_inactive.setdefault("scenario", scenario4)

happy_path = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}

product_dropshipper_happy_path = {**product_dropshipper, **happy_path}
product_supplier_happy_path = {**product_supplier, **happy_path}
product_due_supply_happy_path = {**product_due_supply, **happy_path}

product_dropshipper_happy_path.setdefault("scenario", scenario5)
product_supplier_happy_path.setdefault("scenario", scenario5)
product_due_supply_happy_path.setdefault("scenario", scenario5)
