import random
from datetime import datetime, timedelta

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestData.CommonData.CommonData import CommonData
from TestData.CommonData.CommonDataPromotionAdmin import CommonDataPromotionAdmin
from TestData.DataProvider import NipGenerator, StringGenerator
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    DimensionProductKey,
    DropshippingProductKey,
    DueDeliveryProductKey,
    FilterSetKey,
    FilterTypesKey,
    FrontTestProductsKey,
    PaymentKey,
    WcrProductKey,
)

import settings

products = CommonData.product_variables()
promotions = CommonDataPromotionAdmin()


class PlCommonData:
    @staticmethod
    def common_client() -> dict[str: str]:
        """Returns common client's data used in prod tests for already registered account"""
        register_data = PlCommonData.register_data()
        return {
            "email": "nc-test-user@komputronik.pl",
            "password": "UjK_$CE4pCRB9hjn$_eX",
            "postal_code": register_data["postal_code"],
            "re_captcha": register_data["re_captcha"],
            "company_rules": register_data["company_rules"],
            "marketing_terms": register_data["marketing_terms"]
        }

    @staticmethod
    def register_data(netcorner_domain: bool = True) -> dict[str, str | bool]:
        if settings.server_type == "demo":
            netcorner_domain = False  # MailHog demo does not support the NC email domain (Undelivered Mail exception)

        domain = "test.netcorner.pl" if netcorner_domain else "test.pl"
        email = f"{StringGenerator().generated_string}@{domain}"

        return {
            "email": email,
            "password": "test123!",
            "postal_code": "62-052",
            "re_captcha": True,
            "company_rules": True,
            "marketing_terms": False,
        }

    @staticmethod
    def purchaser_data() -> dict[str: str]:
        return {
            "name": "Jan",
            "surname": "Nabywca",
            "phone": "527600700",
            "mail": "jan.nabywca@test.netcorner.pl",
            "postal_code": "60-003",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Jan Nabywca Company",
            "country": "Polska",
            "nip": NipGenerator().nip,
            "nip_non_gus": "1111111111",
        }

    @staticmethod
    def purchaser_data_non_gus() -> dict[str: str]:
        return {
            "name": "Jan",
            "surname": "Nabywca",
            "phone": "527600700",
            "mail": "jan.nabywca@test.netcorner.pl",
            "postal_code": "5020",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Jan Nabywca Company",
            "country": "Austria",
            "nip": NipGenerator().nip,
            "nip_non_gus": "1111111111",
        }

    @staticmethod
    def purchaser_data_ktpl() -> dict[str: str]:
        return {
            "name": "Jan",
            "surname": "Nabywca",
            "phone": "500600700",
            "mail": "jan.nabywca@test.netcorner.pl",
            "postal_code": "61-693",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Jan Nabywca Company",
            "nip": "9720902729",
            "nip_non_gus": "1111111111",
        }

    @staticmethod
    def purchaser_data_gus() -> dict[str: str]:
        return {
            "name": "Tomasz",
            "surname": "Bolt",
            "phone": "500600700",
            "mail": "maciejguru@test.com",
            "postal_code": "61-255",
            "city": "Poznań",
            "street_name": "Test-Krucza",
            "street_number": "72/34",
            "company": '"LOGSOFT" TOMASZ XXXXXXXX',
            "nip_gus": "9720894467",
        }

    @staticmethod
    def receiver_data() -> dict[str: str]:
        return {
            "name": "Janusz",
            "surname": "Odbiorca",
            "phone": "500600700",
            "mail": "janusz.odbiorca@test.netcorner.pl",
            "postal_code": "61-693",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Janusz Odbiorca Company"
        }

    @staticmethod
    def receiver_data_ktpl() -> dict[str: str]:
        return {
            "name": "Janusz",
            "surname": "Odbiorca",
            "phone": "500600700",
            "mail": "janusz.odbiorca@test.netcorner.pl",
            "postal_code": "61-693",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Janusz Odbiorca Company",
            "nip": "9720902729",
            "nip_non_gus": "1111111111",
        }

    @staticmethod
    def receiver_data_postcode_list() -> dict[str: str]:
        return {
            "name": "Janusz",
            "surname": "Odbiorca",
            "phone": "500600700",
            "mail": "janusz.odbiorca@test.netcorner.pl",
            "postal_code": "62-030",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Janusz Odbiorca Company"
        }

    @staticmethod
    def receiver_data_postcode_matrix() -> dict[str: str]:
        return {
            "name": "Janusz",
            "surname": "Odbiorca",
            "phone": "500600700",
            "mail": "janusz.odbiorca@test.netcorner.pl",
            "postal_code": "60-001",
            "city": "Poznań",
            "street_name": "Wołczyńska",
            "street_number": "37/1",
            "company": "Janusz Odbiorca Company"
        }

    @staticmethod
    def promotion() -> dict[str, str]:
        return {
            "login": "test",
            "password": "test123!@#",
            "login-operator": "test-operator",
        }

    @staticmethod
    def variables(test_storehouses=False) -> dict:
        variables = {
            "cart_product": "product/18600009/-test-product-tcl-u60p6026.html",
            "categories_in_header": ["Laptopy i komputery", "Sprzęt PC", "Akcesoria", "Gaming",
                                     "Telefony i Smartwatche",
                                     "Firma", "AGD", "RTV", "Smarthome", "Foto", "Dziecko", "Lifestyle"],
            "components_minimal": ["Procesor", "Karta graficzna", "Płyta główna", "Dysk"],
            "components_montage": ["Procesor", "Karta graficzna", "Płyta główna", "Pamięć RAM", "Dysk", "Zasilacz",
                                   "Obudowa"],
            "components_set": ["Procesor", "Karta graficzna", "Płyta główna"],
            "components_all": ["Procesor", "Karta graficzna", "Płyta główna", "Pamięć RAM", "Dysk", "Zasilacz",
                               "Obudowa"],
            "components_optional": ["Myszka", "Klawiatura", "Monitor LCD"],
            "delivery_city_poznan": "60-001",
            "delivery_city_komorniki": "Komorniki",
            "delivery_point_saloon": "Poznań Outlet",
            "delivery_point_partner_storehouse": "Swarzędz",
            "delivery_point_poznan_plaza": "Plaza",
            "delivery_point_inpost": "Jugowiec",
            "delivery_point_dhlps": "62-052 KOMORNIKI",
            "order_status_one_work_day": "Wysyłamy najczęściej w 1 dzień roboczy",
            "order_status_on_request": "Towar na zamówienie",
            "order_status_1_or_2_days": "Wysyłka 1-2 dni robocze",
            "order_status_usually_1_or_2_days": "Wysyłka najczęściej w 1-2 dni",
            "order_status_digital": "Licencja elektroniczna",
            "order_status_due_delivery": "Dostawa towaru",
            "order_status_3_to_5_days": "Dostarczamy najczęściej w 3-5 dni!",
            "order_status_dropshipping": "Wysyłka w 2-3 dni",
            "order_status_wcr": "Wydłużony czas realizacji",
            "product_code": products["product_code"],
            "product_code_configurator": products["product_code_configurator"],
            "product_code_promo": products["product_code_promo"],
            "product_code_promo_incorrect": products["product_code_promo_incorrect"],
            "product_code_promo_other": products["product_code_promo_other"],
            "product_code_other": products["product_code_other"],
            "sort_type_price_asc": "price_ascending",
            "sort_type_price_desc": "price_descending",
            "sort_type_name_asc": "name_ascending",
            "sort_type_name_desc": "name_descending",
            "search_phrase_amd": "amd",
            "search_phrase_intel": "intel",
            "search_phrase_apple": "apple",
            "search_phrase_charger": "ładowark",
            "search_suggestions_samsung": "samsung",
            "search_suggestions_displays": "monitory",
            "outlet_offer": "oferta Outlet",
        }
        if test_storehouses:
            variables["delivery_point_saloon"] = "test-storehouse-08"
        return variables

    @staticmethod
    def category_tree_variables(root: str = "", first_lvl: str = "", second_lvl: str = "", third_lvl: str = "") \
            -> dict[str: str]:
        return {"root": root, "first_level": first_lvl, "second_level": second_lvl, "third_level": third_lvl}

    @staticmethod
    def forms_common_data_set() -> dict[str: dict[str: str]]:
        return {
            "forms_empty_form": {
                "name": "", "surname": "", "phone": "", "mail": "", "postal_code": "", "city": "", "street_name": "",
                "street_number": "", "country": "", "company": "", "nip": ""
            },
            "forms_empty_form_non_gus": {
                "name": "", "surname": "", "phone": "", "mail": "", "postal_code": "", "city": "", "street_name": "",
                "street_number": "", "country": "", "company": "", "nip_non_gus": ""
            },
            "forms_empty_form_expected_errors": {
                "name": "Pole jest wymagane", "surname": "Pole jest wymagane", "phone": "Pole jest wymagane",
                "mail": "Pole jest wymagane", "postal_code": "Pole jest wymagane", "city": "Pole jest wymagane",
                "street_name": "Pole jest wymagane", "street_number": "Pole jest wymagane", "country": "",
                "company": "Pole jest wymagane", "nip": "Pole jest wymagane"
            },
            "forms_one_character": {
                "name": "a", "surname": "a", "phone": "a", "mail": "a", "postal_code": "a", "city": "a",
                "street_name": "a", "street_number": "a", "country": "Kanada", "company": "a", "nip": "a"
            },
            "forms_one_character_expected_errors": {
                "name": "Minimalna liczba znaków: 3", "surname": "Minimalna liczba znaków: 2",
                "phone": "Pole jest wymagane", "mail": "Podaj właściwy adres e-mail",
                "postal_code": "Pole jest wymagane",
                "city": "Pole jest wymagane", "street_name": "Minimalna liczba znaków: 2", "country": "",
                "company": "Minimalna liczba znaków: 2", "nip": "Niepoprawny NIP"
            },
            "forms_special_characters": {
                "name": "!@#", "surname": "!@#", "phone": "!@#", "mail": "!@#", "postal_code": "!@#", "city": "!@#",
                "street_name": "!@#", "street_number": "!@#", "country": "Kanada", "company": "!@#", "nip": "!@#"
            },
            "forms_special_characters_expected_errors": {
                "name": "Użyj znaków od A-Z", "surname": "Użyj znaków od A-Z", "phone": "Pole jest wymagane",
                "mail": "Podaj właściwy adres e-mail", "postal_code": "Pole jest wymagane",
                "city": "Pole jest wymagane",
                "street_name": "Użyj znaków od A-Z oraz 0-9", "street_number": "Niepoprawne znaki", "country": "",
                "nip": "Pole jest wymagane"
            },
            "forms_numeric_characters": {
                "name": "1234", "surname": "1234", "phone": "1234", "mail": "1234", "postal_code": "1234",
                "city": "1234", "street_name": "1234", "street_number": "1234", "country": "Kanada", "company": "1234",
                "nip": "1234"
            },
            "forms_numeric_characters_expected_errors": {
                "name": "Użyj znaków od A-Z", "surname": "Użyj znaków od A-Z", "phone": "Podaj właściwy numer",
                "mail": "Podaj właściwy adres e-mail", "postal_code": "Niepoprawny kod", "country": "",
                "city": "Pole jest wymagane", "nip": "Niepoprawny NIP"
            },
            "forms_alfa_numeric_characters": {
                "name": "1234aaaa", "surname": "1234aaaa", "phone": "1234aaaa", "mail": "1234aaaa",
                "postal_code": "1234aaaa", "city": "1234aaaa", "street_name": "1234aaaa", "street_number": "1234aaaa",
                "country": "Kanada", "company": "1234aaaa", "nip": "1234aaaa"
            },
            "forms_alfa_numeric_characters_expected_errors": {
                "name": "Użyj znaków od A-Z", "surname": "Użyj znaków od A-Z", "phone": "Podaj właściwy numer",
                "mail": "Podaj właściwy adres e-mail", "postal_code": "Niepoprawny kod", "country": "",
                "city": "Pole jest wymagane", "nip": "Niepoprawny NIP"
            },
            "forms_wrong_phone_number": {
                "name": "test", "surname": "testowy", "mail": "test@test.pl", "city": "Poznań",
                "street_name": "testowa", "street_number": "12", "postal_code": "60001", "phone": "012123456",
                "country": "Kanada", "company": "test company", "nip": "1231231231"
            },
            "forms_wrong_phone_number_expected_errors_private": {
                "phone": "Podaj właściwy numer"
            },
            "forms_wrong_phone_number_expected_errors_company": {
                "phone": "Podaj właściwy numer", "nip": "Niepoprawny NIP"
            },
            "forms_wrong_phone_number_expected_errors": {
                "phone": "Podaj właściwy numer",
            },
            "forms_wrong_phone_number_expected_errors_company_purchaser": {
                "alert_1": "Niepoprawny NIP", "alert_2": "Podaj właściwy numer"
            },
            "forms_correct_data_private": {
                "name": "test", "surname": "testowy", "mail": "test@test.pl", "city": "Poznań",
                "street_name": "testowa", "street_number": "12", "postal_code": "60001", "phone": "777777777",
                "country": "Kanada", "company": "test company", "nip": "1231231231"
            },
            "forms_correct_data_private_expected_errors": {
                "name": "", "surname": "", "phone": "",
                "mail": "", "postal_code": "", "country": "",
                "city": "", "nip": ""
            },
            "forms_correct_data_company": {
                "name": "test", "surname": "testowy", "mail": "test@test.pl", "city": "Quebec",
                "street_name": "testowa", "street_number": "12", "postal_code": "V5G4V4", "phone": "12345678901",
                "country": "Kanada", "company": "test company", "nip": "1231231231"
            },
            "forms_correct_data_company_expected_errors": {
                "name": "", "surname": "", "phone": "",
                "mail": "", "postal_code": "", "country": "",
                "city": "", "nip": ""
            }
        }

    @staticmethod
    def forms_register_data_set() -> dict[str: dict[str: str]]:
        return {
            "forms_empty_form": {
                "email": "", "password": ""
            },
            "forms_empty_form_expected_errors": {
                "email": "Pole jest wymagane", "password": "Pole jest wymagane"
            },
            "forms_one_character": {
                "email": "a", "password": "a"
            },
            "forms_one_character_expected_errors": {
                "email": "Podaj właściwy adres e-mail", "password": "Min. 6 znaków, przynajmniej jedna cyfra i litera"
            },
            "forms_same_login_twice": {
                "email": f"{StringGenerator().generated_string}@test.netcorner.pl",
                "password": "test123!",
            },
            "forms_same_login_twice_expected_errors": {
                "email": "Login jest już w użyciu"
            },
        }

    @staticmethod
    def footer_various_elements() -> dict[str: dict[str: str]]:
        return {
            "phone_number": "+48 61 668 00 07",
            "social_platforms": ['facebook', 'instagram', 'youtube', 'x', 'tiktok'],
        }

    @staticmethod
    def footer_social_section_items() -> dict[str: dict[str: str]]:
        return {
            "facebook": "https://www.facebook.com/komputronik",
            "instagram": "https://www.instagram.com/Komputronik/",
            "youtube": "https://www.youtube.com/user/KomputronikSA",
            "x": "https://x.com/Komputronik_pl",
            "tiktok": "https://www.tiktok.com/@komputronik_pl"
        }

    @staticmethod
    def footer_information_elements() -> dict[str: dict[str: str]]:
        return {
            "Regulamin": "informacje/pomoc/regulamin-polityka/",
            "Pomoc": "informacje/pomoc/",
            "Polityka prywatności": "informacje/pomoc/regulamin-polityka/",
            "Zarządzanie zgodami": "customer/account/customer-consents",
            "Program partnerski": "lp/program-partnerski/",
            "Mapa strony": "sitemap",
            "Nano": "https://nano.komputronik.pl/",
            "Komputronik Gaming": "https://gaming.komputronik.pl/"
        }

    @staticmethod
    def footer_client_service_items() -> dict[str: dict[str: str]]:
        return {
            "Serwis - reklamacje": "informacje/pomoc/reklamacje/",
            "Raty": "informacje/uslugi/raty/",
            "Leasing": "informacje/leasing-laptopow-komputerow-leasing-it/",
            "Dostawa": "informacje/pomoc/dostawa/",
            "Zwroty towarów": "informacje/pomoc/zwroty/",
            "Utylizacja zepsutego sprzętu": "informacje/pomoc/utylizacja/"
        }

    @staticmethod
    def footer_shopping_items() -> dict[str: dict[str: str]]:
        return {
            "Promocje": "informacje/promocje/",
            "Konfigurator PC": "advanced-configurator/",
            "Poradniki zakupowe": "informacje/",
            "Aktualności": "informacje/aktualnosci/",
            "Outlet": "promocje/outlet",
            "Oferta dla firm (B2B)": "lp/oferta-dla-firm/",
            "Aplikacja": "lp/aplikacja/",
        }

    @staticmethod
    def footer_about_us_items() -> dict[str: dict[str: str]]:
        return {
            "Kontakt": "informacje/kontakt/",
            "Kariera": "https://kariera.komputronik.com/",
            "Biuro Prasowe": "https://aktualnosci.komputronik.com/",
            "Współpraca Agencja/Franczyza": "https://www.komputronik.com/wspolpraca/",
            "Klienci hurtowi": "https://d.ktr.pl/",
            "Relacje inwestorskie": "https://www.komputronik.com/raporty/",
        }

    @staticmethod
    def cart_variables(test_storehouses=False) -> dict[str: str | int]:
        variables = {
            "warehouse_name_magazyn_glowny": "- Magazyn Główny -",
            "warehouse_name_gniezno": "Gniezno",
            "warehouse_name_gdynia_ch_kwiatkowski": "Gdynia CH Kwiatkowski",
            "warehouse_name_wawa_megastore": "Warszawa Megastore",
            "warehouse_name_swarzedz_partnerski": "Swarzędz Partnerski",
            "warehouse_name_poznan_stary_browar": "Poznań Stary Browar",
            "warehouse_name_gdansk_ch_baltycka": "Gdańsk Galeria Bałtycka",
            "warehouse_name_krakow_m1": "Kraków M1",
            "warehouse_name_wolsztyn_partnerski": "Wolsztyn partnerski",
            "delivery_method_inpost": "inpost",
            "delivery_method_dhlpop": "dhlpop",
            "delivery_name_courier": "Kurier",
            "delivery_name_inpost": "InPost",
            "delivery_name_dhlpop": "ParcelShop",
            "delivery_name_without_lift": "Przesyłka wielkogabarytowa - dostawa bez wniesienia",
            "delivery_name_with_lift": "Przesyłka wielkogabarytowa - z wniesieniem do lokalu",
            "delivery_location_postal_60001": "60-001",
            "delivery_location_postal_61131": "61-131",
            "delivery_location_gniezno": "Gniezno",
            "delivery_location_gdynia": "Gdynia",
            "delivery_location_warszawa": "Warszawa",
            "delivery_location_pruszkow": "Pruszków",
            "delivery_location_poznan": "Poznań",
            "delivery_location_swarzedz": "Swarzędz",
            "delivery_location_gdansk": "Gdańsk",
            "delivery_location_wolsztyn": "Wolsztyn",
            "delivery_location_krakow": "Kraków",
            "delivery_point_name_poznan_outlet": "Outlet Komorniki",
            "delivery_point_name_gniezno": "Gniezno",
            "delivery_point_name_gdynia": "Gdynia",
            "delivery_point_name_gniezno_inpost": "GNI01A",
            "delivery_point_name_poznan_inpost": "POZ77M",
            "delivery_point_name_poznan_inpost_2": "POZ01N",
            "delivery_point_name_poznan_dhlpop": "DHL POP ŻABKA",
            "delivery_point_name_gniezno_dhlpop": "DHL POP ŻABKA",
            "delivery_point_name_poznan_stary_browar": "StaryBrowar",
            "delivery_point_name_poznan_malta": "PoznanMalta",
            "delivery_point_name_wawa_megastore": "WarszawaMegastore",
            "delivery_point_name_swarzedz": "Swarzędz",
            "delivery_point_name_gdansk_ch_baltycka": "Gdansk_CH_Baltycka",
            "delivery_point_name_krakow_m1": "Krakow_M1",
            "delivery_point_name_wolsztyn": "Wolsztyn",
            "product_number_01": 1,
            "product_number_02": 2,
            "product_number_03": 3,
            "product_number_04": 4,
            "product_number_05": 5,
            "product_number_06": 6,
            "product_number_07": 7,
            "product_number_08": 8,
            "product_number_09": 9,
            "product_number_10": 10,
            "product_number_11": 11,
            "product_number_12": 12,
            "product_number_13": 13,
            "product_number_14": 14,
            "product_number_15": 15,
            "product_number_16": 16,
            "product_number_17": 17,
            "product_number_18": 18,
            "product_markup_DW": "DW",
            "product_markup_ND": "ND",
        }
        if test_storehouses:
            variables["delivery_point_name_poznan_outlet"] = "test-storehouse-08"
            variables["delivery_point_name_gniezno"] = "test-storehouse-04"
            variables["delivery_point_name_gdynia"] = "test-storehouse-01"
            variables["delivery_point_name_poznan_stary_browar"] = "test-storehouse-02"
            variables["delivery_point_name_poznan_malta"] = "test-storehouse-06"
            variables["delivery_point_name_wawa_megastore"] = "test-storehouse-10"
            variables["delivery_point_name_swarzedz"] = "test-storehouse-07"
            variables["delivery_point_name_gdansk_ch_baltycka"] = "test-storehouse-03"
            variables["delivery_point_name_krakow_m1"] = "test-storehouse-12"
            variables["delivery_point_name_wolsztyn"] = "test-storehouse-05"
        return variables

    @staticmethod
    def payments() -> dict[PaymentKey: str]:
        return {
            PaymentKey.CARD_POLCARD: "Karta płatnicza",
            PaymentKey.BLIK: "BLIK",
            PaymentKey.CASH: "Gotówka",
            PaymentKey.ELECTRONIC_TRANSFER: "Szybki przelew",
            PaymentKey.TRANSFER: "przedpłata",
            PaymentKey.SPLIT_PAYMENT: "SplitPayment"
        }

    @staticmethod
    def dimension_products() -> dict[DimensionProductKey: int]:
        return {
            DimensionProductKey.GN: 500000001,
            DimensionProductKey.G6: 500000002,
            DimensionProductKey.G1W: 500000003,
            DimensionProductKey.G1: 500000004,
        }

    @staticmethod
    def wcr_products() -> dict[WcrProductKey: int]:
        return {
            WcrProductKey.WCR_ND: 500000101,
            WcrProductKey.WCR_DW: 500000102,
            WcrProductKey.WCR_ND_STOCK: 500000103,
            WcrProductKey.WCR_DW_STOCK: 500000104
        }

    @staticmethod
    def dropshipping_products() -> dict[DropshippingProductKey: int]:
        return {
            DropshippingProductKey.DROPSHIPPING: 510000001,
            DropshippingProductKey.SUPPLIER: 510000002,
            DropshippingProductKey.DUE_SUPLY: 510000003,
            DropshippingProductKey.DROPSHIPPING_ADV_1: 510000004,
            DropshippingProductKey.DROPSHIPPING_ADV_2: 510000005,
            DropshippingProductKey.DROPSHIPPING_ADV_3: 510000006,
            DropshippingProductKey.DROPSHIPPING_ADV_4: 510000007
        }

    @staticmethod
    def due_delivery_products() -> dict[DueDeliveryProductKey: int]:
        return {
            DueDeliveryProductKey.ND_N_DUE_DELIVERY: 500000201,
            DueDeliveryProductKey.DW_N_DUE_DELIVERY: 500000202,
            DueDeliveryProductKey.NDA_N_DUE_DELIVERY: 500000203,
            DueDeliveryProductKey.AKA_N_DUE_DELIVERY: 500000204,
            DueDeliveryProductKey.ND_N_OVERDUE_DELIVERY: 500000205,
            DueDeliveryProductKey.DW_N_OVERDUE_DELIVERY: 500000206,
            DueDeliveryProductKey.NDA_N_OVERDUE_DELIVERY: 500000207,
            DueDeliveryProductKey.AKA_N_OVERDUE_DELIVERY: 500000208,
            DueDeliveryProductKey.N_DUE_DELIVERY: 500000209,
            DueDeliveryProductKey.N_OVERDUE_DELIVERY: 500000210
        }

    @staticmethod
    def front_test_products() -> dict[FrontTestProductsKey: str]:
        return {
            FrontTestProductsKey.MIN_QTY_PRODUCT: 500000510,
            FrontTestProductsKey.MIN_QTY_PRODUCT_W_UNIT_PRICE: 500000511,
            FrontTestProductsKey.OZO_PRODUCT: 500000513,
        }

    @staticmethod
    def alerts() -> dict[str: str]:
        return {
            "alert_cok": "Wybranych produktów nie można obecnie kupić za pośrednictwem sklepu internetowego.",
            "alert_split_order": "Produkty w koszyku znajdują się w różnych magazynach.",
            "alert_limited_stock": "Produkt {} nie jest dostępny w podanej liczbie",
            "alert_exhibition": "W Twoim koszyku znajdują się produkty z ekspozycji.",
            "alert_no_shipping_methods": "Brak dostępnych form dostawy",
            "alert_cart_price_changed": "uległa zmianie"
        }

    @staticmethod
    def toasts() -> dict[str: str]:
        return {
            "stocks_exceeded": "nie jest dostępny w podanej liczbie",
        }

    @staticmethod
    def cart_restrictions_variables() -> dict[str: list[DeliveryMethodKey]]:
        inpost = DeliveryMethodKey.INPOST
        delivery = DeliveryMethodKey.COURIER
        storehouses = DeliveryMethodKey.STOREHOUSE
        dhlpop = DeliveryMethodKey.DHLPOP
        return {
            "inpost": [inpost],
            "dhlpop": [dhlpop],
            "storehouses": [storehouses],
            "delivery": [delivery],
            "storehouses_delivery": [storehouses, delivery],
            "storehouses_delivery_dhlpop": [storehouses, delivery, dhlpop],
            "storehouses_delivery_inpost_dhlpop": [storehouses, delivery, inpost, dhlpop],
            "dropshipping": [storehouses, delivery, inpost]
        }

    @staticmethod
    def aggregator_category_element_data() -> dict[str: str | bool]:
        return {
            "name": "Laptopy",
            "code": "Agregator",
            "category": True,
            "category_choose": True
        }

    @staticmethod
    def aggregator_products_element_data() -> dict[str: str | bool]:
        return {
            "name": "Klawiatury",
            "code": "Agregator",
            "products": True,
            "products_choose": "KL-NAT-038, {},LT-STD-I15-DEL-1300".format(CommonData.product_variables()["product_code_promo"])
        }

    @staticmethod
    def aggregator_data_category() -> dict[str: str | bool]:
        return {
            "name": "Agregator dla kategorii",
            "url": f"{StringGenerator().generated_string}agregatcategory",
            "published": True,
            "channel_type": True
        }

    @staticmethod
    def aggregator_data_products() -> dict[str: str | bool]:
        return {
            "name": "Agregator dla produktów",
            "url": f"{StringGenerator().generated_string}agregatproducts",
            "published": True,
            "channel_type": True
        }

    @staticmethod
    def courier_matrix_delivery_assertions() -> list[str]:
        return [
            "Kurier", "Dostawa paczek"
        ]

    @staticmethod
    def filters() -> dict[str: str | CommonBasePageObject.ListCommon]:
        return {
            FilterSetKey.REDUCED_PRICE: {
                FilterTypesKey.PROMOTION: ["Produkty w niższej cenie"]
            },
            FilterSetKey.DIGITAL_LICENSE: {
                FilterTypesKey.PRODUCT_VERSION: ["elektroniczna"],
                FilterTypesKey.CARRIED_BY: ["do pobrania"],
                FilterTypesKey.LICENCE_TYPE: ["nowa licencja"]
            },
            FilterSetKey.PENDRIVE: {
                FilterTypesKey.PRODUCER: ["Kingston", "Sandisk"],
                FilterTypesKey.INTERFACE: ["USB 3.0"],
                FilterTypesKey.PRICE: ["1", "50"]
            },
            FilterSetKey.PHILIPS: {
                FilterTypesKey.PRODUCER: ["Philips"]
            },
            FilterSetKey.KINGSTON: {
                FilterTypesKey.PRODUCER: ["Kingston"]
            },
            FilterSetKey.SUUNTO: {
                FilterTypesKey.PRODUCER: ["Suunto"]
            },
            FilterSetKey.AMD: {
                FilterTypesKey.PRODUCER: ["AMD"]
            },
            FilterSetKey.MSI: {
                FilterTypesKey.PRODUCER: ["MSI"]
            },
            FilterSetKey.INTEL: {
                FilterTypesKey.PRODUCER: ["Intel"]
            },
            FilterSetKey.SAMSUNG: {
                FilterTypesKey.PRODUCER: ["Samsung"]
            }
        }

    @staticmethod
    def split_payment_activation_value() -> int:
        return 15000

    @staticmethod
    def default_ozo_promotion() -> dict:
        return {
            "name": "OzO Limited Sale Promotion {}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            "value": 1,
            "date_from": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "date_to": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M"),
            "sold_amount": 3,
            "total_amount": 50,
            "per_one_customer": 1,
        }

    @staticmethod
    def default_partner_group_qr() -> dict:
        return {
            "group_name": "Test Partner Group QR created: {}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            "enable_qr_code": True,
            "price_category": "employee",
        }

    @staticmethod
    def default_partner_group_sms() -> dict:
        return {
            "group_name": "Test Partner Group SMS created: {}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            "enable_qr_code": False,
            "price_category": "employee",
            "sms_message": "Link do zalogowania:",
        }

    @staticmethod
    def random_phone_numbers(count: int = 10) -> list[str]:
        mobile_prefixes = [
            "50", "51", "53", "57", "60", "66", "69",
            "72", "73", "78", "79", "88"
        ]
        numbers = []
        for _ in range(count):
            prefix = random.choice(mobile_prefixes)
            remaining_digits = "".join(str(random.randint(0, 9)) for _ in range(7))
            numbers.append(prefix + remaining_digits)
        return numbers
