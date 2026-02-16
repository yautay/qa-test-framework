from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    DimensionProductKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_big_size = "Scenariusz: \n" \
                    "   1. Z kategorii produktów testowych iterując wybiera produkt spełniający wszystkie kryteria:\n" \
                    "       a. z dostępnym wniesieniem do lokalu,\n" \
                    "       b. z wysyłką w 1 dzień roboczy,\n" \
                    "       c. niebędący w sprzedaży limitowanej,\n" \
                    "       d. nie będący ofertą outlet.\n" \
                    "   2. Dodaje produkt do koszyka.\n" \
                    "   3. W procesie zakupowym weryfikuje dostępność metody z wniesieniem.\n" \
                    "   4. Zamawia produkt z usługą wniesienia.\n" \
                    "   5. Z poziomu admina sklepu weryfikuje złożone zamówienie\n"

scenario_big_size_not_available = "Scenariusz: \n" \
                                  "   1. Z kategorii produktów testowych iterując wybiera produkt spełniający wszystkie kryteria:\n" \
                                  "       a. z dostępnym wniesieniem do lokalu,\n" \
                                  "       b. z wysyłką w 1 dzień roboczy,\n" \
                                  "       c. niebędący w sprzedaży limitowanej,\n" \
                                  "       d. nie będący ofertą outlet.\n" \
                                  "   2. Dodaje produkt do koszyka.\n" \
                                  "   3. W procesie zakupowym weryfikuje dostępność metody z wniesieniem.\n" \
                                  "   4. Zamawia produkt bez usługi wniesienia.\n" \
                                  "   5. Z poziomu admina sklepu weryfikuje złożone zamówienie\n"

common_test_data = {
    "product": DimensionProductKey.G1,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "register_data": PlCommonData.register_data(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()}
}
order_big_size = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
order_big_size_without_lift = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITHOUT_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}

order_big_size.update(common_test_data.copy())
order_big_size_without_lift.update(common_test_data.copy())

order_big_size.setdefault("scenario", scenario_big_size)
order_big_size_without_lift.setdefault("scenario", scenario_big_size_not_available)
