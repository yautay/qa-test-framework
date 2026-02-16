import copy

from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    DimensionProductKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Testy modułu gabarytów cz.1 - pojedyncze produkty\"\n" \
            "   1. Loguje się na klienta.\n" \
            "   2. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   3. Sprawdza czy są widoczne odpowiednie metody transportu.\n" \
            "   4. Składa zamówienie jako zalogowany klient na wybraną metodę transportu"

scenario2 = "Scenariusz: \n" \
            "Testy modułu gabarytów cz.2 - nakładające się produkty\"\n" \
            "   1. Loguje się na klienta.\n" \
            "   2. Otwiera pierwszy produkt i dodaje go do koszyka.\n" \
            "   3. Otwiera drugi produkt i dodaje go do koszyka.\n" \
            "   4. Sprawdza czy są widoczne odpowiednie metody transportu.\n" \
            "   5. Składa zamówienie jako zalogowany klient na wybraną metodę transportu."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_dim_products = PlCommonData.dimension_products()
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER}

test_1a = {
    "test_name": "in_cart_GN",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": None,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_1a.update(copy.deepcopy(common_test_data))
test_1a.setdefault("scenario", scenario1)

test_1b = {
    "test_name": "in_cart_GN",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": None,
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_1b.update(copy.deepcopy(common_test_data))
test_1b.setdefault("scenario", scenario1)

test_2a = {
    "a": "test",
    "test_name": "in_cart_G6",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": None,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]}}
test_2a.update(copy.deepcopy(common_test_data))
test_2a.setdefault("scenario", scenario1)

test_2b = {
    "test_name": "in_cart_G6",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": None,
    "delivery_object": {
        "order_with": DeliveryMethodKey.INPOST,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_inpost_2"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]}}
test_2b.update(copy.deepcopy(common_test_data))
test_2b.setdefault("scenario", scenario1)

test_3a = {
    "test_name": "in_cart_G1W",
    "product_first": pl_dim_products[DimensionProductKey.G1W],
    "product_second": None,
    "delivery_object": {
        "order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
        "receiver_data": PlCommonData.receiver_data(),
        "receiver_type": ReceiverKey.PRIVATE,
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_3a.update(copy.deepcopy(common_test_data))
test_3a.setdefault("scenario", scenario1)

test_3b = {
    "test_name": "in_cart_G1W",
    "product_first": pl_dim_products[DimensionProductKey.G1W],
    "product_second": None,
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_3b.update(copy.deepcopy(common_test_data))
test_3b.setdefault("scenario", scenario1)

test_4a = {
    "test_name": "in_cart_G1",
    "product_first": pl_dim_products[DimensionProductKey.G1],
    "product_second": None,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_4a.update(copy.deepcopy(common_test_data))
test_4a.setdefault("scenario", scenario1)

test_4b = {
    "test_name": "in_cart_G1",
    "product_first": pl_dim_products[DimensionProductKey.G1],
    "product_second": None,
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_4b.update(copy.deepcopy(common_test_data))
test_4b.setdefault("scenario", scenario1)

test_11a = {
    "test_name": "in_cart_GN_and_GN",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.GN],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_11a.update(copy.deepcopy(common_test_data))
test_11a.setdefault("scenario", scenario2)

test_11b = {
    "test_name": "in_cart_GN_and_GN",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.GN],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_11b.update(copy.deepcopy(common_test_data))
test_11b.setdefault("scenario", scenario2)

test_12a = {
    "test_name": "in_cart_GN_and_G6",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.G6],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_12a.update(copy.deepcopy(common_test_data))
test_12a.setdefault("scenario", scenario2)

test_12b = {
    "test_name": "in_cart_GN_and_G6",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.G6],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_12b.update(copy.deepcopy(common_test_data))
test_12b.setdefault("scenario", scenario2)

test_13a = {
    "test_name": "in_cart_GN_and_G1W",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.G1W],
    "delivery_object": {
        "order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
        "receiver_data": PlCommonData.receiver_data(),
        "receiver_type": ReceiverKey.PRIVATE,
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_13a.update(copy.deepcopy(common_test_data))
test_13a.setdefault("scenario", scenario2)

test_13b = {
    "test_name": "in_cart_GN_and_G1W",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.G1W],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_13b.update(copy.deepcopy(common_test_data))
test_13b.setdefault("scenario", scenario2)

test_14a = {
    "test_name": "in_cart_GN_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_14a.update(copy.deepcopy(common_test_data))
test_14a.setdefault("scenario", scenario2)

test_14b = {
    "test_name": "in_cart_GN_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.GN],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_14b.update(copy.deepcopy(common_test_data))
test_14b.setdefault("scenario", scenario2)

test_22a = {
    "test_name": "in_cart_G6_and_G6",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": pl_dim_products[DimensionProductKey.G6],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]}}
test_22a.update(copy.deepcopy(common_test_data))
test_22a.setdefault("scenario", scenario2)

test_22b = {
    "test_name": "in_cart_G6_and_G6",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": pl_dim_products[DimensionProductKey.G6],
    "delivery_object": {
        "order_with": DeliveryMethodKey.INPOST,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_inpost_2"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]}}
test_22b.update(copy.deepcopy(common_test_data))
test_22b.setdefault("scenario", scenario2)

test_23a = {
    "test_name": "in_cart_G6_and_G1W",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": pl_dim_products[DimensionProductKey.G1W],
    "delivery_object": {
        "order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
        "receiver_data": PlCommonData.receiver_data(),
        "receiver_type": ReceiverKey.PRIVATE,
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_23a.update(copy.deepcopy(common_test_data))
test_23a.setdefault("scenario", scenario2)

test_23b = {
    "test_name": "in_cart_G6_and_G1W",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": pl_dim_products[DimensionProductKey.G1W],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_23b.update(copy.deepcopy(common_test_data))
test_23b.setdefault("scenario", scenario2)

test_24a = {
    "test_name": "in_cart_G6_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_24a.update(copy.deepcopy(common_test_data))
test_24a.setdefault("scenario", scenario2)

test_24b = {
    "test_name": "in_cart_G6_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.G6],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_24b.update(copy.deepcopy(common_test_data))
test_24b.setdefault("scenario", scenario2)

test_33a = {
    "test_name": "in_cart_G1W_and_G1W",
    "product_first": pl_dim_products[DimensionProductKey.G1W],
    "product_second": pl_dim_products[DimensionProductKey.G1W],
    "delivery_object": {
        "order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
        "receiver_data": PlCommonData.receiver_data(),
        "receiver_type": ReceiverKey.PRIVATE,
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_33a.update(copy.deepcopy(common_test_data))
test_33a.setdefault("scenario", scenario2)

test_33b = {
    "test_name": "in_cart_G1W_and_G1W",
    "product_first": pl_dim_products[DimensionProductKey.G1W],
    "product_second": pl_dim_products[DimensionProductKey.G1W],
    "delivery_object": {
        "order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
        "receiver_data": PlCommonData.receiver_data(),
        "receiver_type": ReceiverKey.PRIVATE,
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_33b.update(copy.deepcopy(common_test_data))
test_33b.setdefault("scenario", scenario2)

test_34a = {
    "test_name": "in_cart_G1W_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.G1W],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_34a.update(copy.deepcopy(common_test_data))
test_34a.setdefault("scenario", scenario2)

test_34b = {
    "test_name": "in_cart_G1W_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.G1W],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_34b.update(copy.deepcopy(common_test_data))
test_34b.setdefault("scenario", scenario2)

test_44a = {
    "test_name": "in_cart_G1_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.G1],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_44a.update(copy.deepcopy(common_test_data))
test_44a.setdefault("scenario", scenario2)

test_44b = {
    "test_name": "in_cart_G1_and_G1",
    "product_first": pl_dim_products[DimensionProductKey.G1],
    "product_second": pl_dim_products[DimensionProductKey.G1],
    "delivery_object": {
        "order_with": DeliveryMethodKey.STOREHOUSE,
        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]}}
test_44b.update(copy.deepcopy(common_test_data))
test_44b.setdefault("scenario", scenario2)
