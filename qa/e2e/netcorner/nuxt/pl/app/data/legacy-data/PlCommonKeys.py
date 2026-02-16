from enum import Enum, auto


class ProductKey(Enum):
    pass


class ProductPageAlertKey(Enum):
    LIMITED_SALE_EXCEEDED = auto()
    GENERAL_ALERT = auto()


class PurchaserKey(Enum):
    PRIVATE = "private"
    COMPANY = "company"


class ReceiverKey(Enum):
    PRIVATE = "private"
    COMPANY = "company"


class DeliveryMethodKey(Enum):
    STOREHOUSE = "Odbiór"
    COURIER = "Kurier"
    COURIER_WITHOUT_LIFT = "Przesyłka wielkogabarytowa - dostawa bez wniesienia"
    COURIER_WITH_LIFT = "Przesyłka wielkogabarytowa - z wniesieniem do lokalu"
    INPOST = "InPost"
    DHLPOP = "ParcelShop"
    DIGITAL = "elektroniczna"


class OrderAsKey(Enum):
    ORDER_AS_NON_REGISTERED = "order_as_non_registered"
    ORDER_AS_REGISTERED = "order_as_registered"
    ORDER_AS_LOGGED_IN_CART = "order_as_logged_in_cart"
    ORDER_AS_LOGGED_IN_CART_SKIP_REGISTRATION = "order_as_logged_in_cart_skip_registration"
    JUST_LOG_USER = "just_log_user"


class PaymentKey(Enum):
    CARD_POLCARD = auto()
    ELECTRONIC_TRANSFER = auto()
    BLIK = auto()
    TRANSFER = auto()
    CASH = auto()
    SPLIT_PAYMENT = auto()


class DeliveryMatrixKey(Enum):
    FREE = "0 zł"
    SATURDAY = "+ 24,90 zł"
    WEEK_MORNING = "+ 9,90 zł"


class AlertKey(Enum):
    ALERT_COK = "alert_cok"
    ALERT_SPLIT_ORDER = "alert_split_order"
    ALERT_LIMITED_STOCK = "alert_limited_stock"
    ALERT_EXHIBITION = "alert_exhibition"
    ALERT_NO_SHIPPING_METHODS = "alert_no_shipping_methods"
    ALERT_CART_PRICE_CHANGED = "alert_cart_price_changed"


class ToastKey(Enum):
    STOCKS_EXCEEDED = "stocks_exceeded"


class DueDeliveryProductKey(ProductKey):
    ND_N_DUE_DELIVERY = "SATP1"
    DW_N_DUE_DELIVERY = "SATP2"
    NDA_N_DUE_DELIVERY = "SATP3"
    AKA_N_DUE_DELIVERY = "SATP4"
    ND_N_OVERDUE_DELIVERY = "SATP5"
    DW_N_OVERDUE_DELIVERY = "SATP6"
    NDA_N_OVERDUE_DELIVERY = "SATP7"
    AKA_N_OVERDUE_DELIVERY = "SATP8"
    N_DUE_DELIVERY = "SATP9"
    N_OVERDUE_DELIVERY = "SATP10"


class WcrProductKey(ProductKey):
    WCR_ND = "WCRPRODUCT_ND",
    WCR_DW = "WCRPRODUCT_DW",
    WCR_ND_STOCK = "WCRPRODUCT_ND_STOCK",
    WCR_DW_STOCK = "WCRPRODUCT_DW_STOCK"


class DimensionProductKey(ProductKey):
    GN = "DMTP1"
    G6 = "DMTP2"
    G1W = "DMTP3"
    G1 = "DMTP4"


class DigitalProductKey(ProductKey):
    MOLP = "OP-LE-MS-323"


class PromotionSezamProductKey(ProductKey):
    PROMO_VALUE_PRODUCT = "DMTP3"


class PromotionCodeTypeKey(Enum):
    PROMOTION = ("Promocja", 1)
    PREPAID = ("Przedpłata", 2)
    AFFILIATE = ("Zmiana", 3)
    CONFIGURATOR = ("Promocja", 4)
    AGGREGATOR = ("Promocja", 5)
    PRODUCER = ("Promocja", 6)
    PERCENTAGE = ("Promocja", 7)
    ADDITIONAL = ("Promocja", 8)
    ACTIVITY = ("Promocja", 9)
    PROMOTIONNETTO = ("Promocja", 10)
    PRODUCERNETTO = ("Promocja", 11)
    PERCENTAGENETTO = ("Promocja", 12)
    ADDITIONALNETTO = ("Promocja", 13)
    AGGREGATORNETTO = ("Promocja", 14)
    PUBLIC_A = ("Promocja", 15)
    PUBLIC_B = ("Promocja", 16)
    PUBLIC_C = ("Promocja", 17)


class FilterSetKey(Enum):
    REDUCED_PRICE = "filters_reduced_price_products"
    DIGITAL_LICENSE = "filters_digital_license"
    PENDRIVE = "filters_pendrive"
    PHILIPS = "filters_philips"
    SUUNTO = "filters_suunto"
    AMD = "filters_amd"
    INTEL = "filters_intel"
    SAMSUNG = "filters_samsung"
    KINGSTON = "filters_kingston"
    MSI = "filters_msi"


class FilterTypesKey(Enum):
    LICENCE_TYPE = "rodzaj_licencji"
    PRODUCT_VERSION = "wersja_produktu"
    CARRIED_BY = "nośnik"
    PRODUCER = "producenci"
    INTERFACE = "interfejs"
    PRICE = "cena"
    PROMOTION = "produkt_w_promocji"


class DropshippingProductKey(ProductKey):
    DROPSHIPPING = "DSAB",
    SUPPLIER = "DSMGZEW",
    DUE_SUPLY = "DSDOST",
    DROPSHIPPING_ADV_1 = "DSADV1",
    DROPSHIPPING_ADV_2 = "DSADV2",
    DROPSHIPPING_ADV_3 = "DSADV3",
    DROPSHIPPING_ADV_4 = "DSADV4",


class FrontTestProductsKey(ProductKey):
    MIN_QTY_PRODUCT = "ZESTAW PRODUKTOWY"
    MIN_QTY_PRODUCT_W_UNIT_PRICE = "ZESTAW PRODUKTOWY + CENA JEDN."
    OZO_PRODUCT = "PRODUKT OZO"


class ComponentContextKey(Enum):
    CHECKOUT = "checkout"
    ACCOUNT = "account"


class ButtonNameKey(Enum):
    BOTH = "both"
    PARTS = "parts"
    SET = "set"


class ProductAvailabilityKey(Enum):
    TMP_UNAVAILABLE = "tymczasowo niedostępny"
    UNAVAILABLE = "Towar trwale niedostępny"
    AVAILABLE = "Wysyłamy najczęściej w 1 dzień"
    AVAILABLE_IN_2D = "Wysyłka najczęściej w 1-2 dni robocze"
    AVAILABLE_IN_SELECTED_STORES = "Wysyłka realizowana bezpośrednio z salonu"
    AVAILABLE_LAST_ITEM = "Dostępna 1 szt. Może być na ekspozycji."
    LARGE_QTY = "Dostępna duża ilość"
    AVAILABLE_IN_HQ = "Towar dostępny w centrali, dostawa do tego salonu w 1-2 dni robocze od złożenia zamówienia."
    PUBLIC_CODE = "Cena z kodem:"


class ToastTypeKey(Enum):
    POSITIVE = "toast-positive"
    NEGATIVE = "toast-negative"
    CART_OFFER_NOT_ACTIVE = "Oferta nie jest już aktywna"
    LIMITED_SALE_EXCEEDED = "Przekroczono limit liczby sztuk produktu"
