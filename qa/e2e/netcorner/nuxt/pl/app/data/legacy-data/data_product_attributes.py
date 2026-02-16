import json
import os


class DataProductAttributes:
    """Class contains dictionary with product's date used in cart restriction tests"""
    # +--------------+----------------+---------------------------+
    # |object_flag_id|object_flag_code|object_flag_is_package_size|
    # +--------------+----------------+---------------------------+
    # |8             |G1              |1                          |
    # |9             |G2              |1                          |
    # |34            |G3              |1                          |
    # |45            |GN              |1                          |
    # |46            |G4              |1                          |
    # |47            |G5              |1                          |
    # |48            |G6              |1                          |
    # |49            |G1W             |1                          |
    # +--------------+----------------+---------------------------+

    rel_path = "../../TestData/pl_komputronik_nuxt/cart_restriction_products_specification.json"
    product_db_id = int
    data = {}
    flags_dict = {
        "0": "No flags",
        "4": "W",
        "8": "G1",
        "9": "G2",
        "34": "G3",
        "45": "GN",
        "46": "G4",
        "47": "G5",
        "48": "G6",
        "49": "G1W",
        "1": "V"
    }
    warehouse_dict = {
        "233": "Warszawa Megastore",
        "1": "Magazyn Główny -> 3210",
        "204": "Poznań Outlet"
    }
    price_dict = {
        "10": "Cena internetowa",
        "5": "Cena Hurt D - Patronaty",
    }
    channel_dict = {
        "activity": {
            "1": "active",
            "0": "not active"
        },
        "visibility": {
            "1": "visible",
            "0": "not visible"
        },
        "purchasable": {
            "1": "purchasable",
            "0": "not purchasable"
        },
        "status": {
            "5": "Wysyłamy najczęściej w 1 dzień roboczy / Produkt aktualnie dostępny w naszym magazynie wysyłkowym",
            "6": "Wysyłka w 1-2 dni / Aktualnie towar dostępny jest tylko w niektórych naszych salonach",
            "4": "Towar niedostępny",
            "1": "Towar trwale niedostępny, wyczerpane zapasy magazynowe / Produkt wyprzedany. Brak możliwości zamówienia.",
            "9": "Towar na zamówienie / Towaru nie mamy aktualnie w magazynach, sprowadzimy go dla Ciebie w najbliższym możliwym terminie.",
            "7": "Wysyłka w 4-5 dni / Produkt wyślemy do Ciebie w przeciągu 4-5 dni roboczych.",
            "13": "Towar na zamówienie / Licencja elektroniczna – dostępna na zamówienie.",
            "11": "Wysyłamy najczęściej w 1 dzień roboczy / Licencja elektroniczna – dostępna natychmiast",
            "12": "Wysyłka 2-3 dni/ Licencja elektroniczna – dostępna na magazynie dostawcy"
        }
    }

    def __init__(self, product_db_id):
        self.product_db_id = product_db_id
        directory = os.path.dirname(__file__)
        filename = os.path.join(directory, self.rel_path)
        self.data = json.loads(self.__read_from_file(filename))

    def get_product_attributes(self):
        """Returns to console deserialized data form product database entries"""
        product_id = self.product_db_id
        erp_code = self.data["ktr_product"][product_id]["product_code_max"]
        product_code = self.data["ktr_product"][product_id]["product_code"]
        product_name = self.data["ktr_product_i18n"][product_id]["product_i18n_name"]
        product_flag = self.__get_flag()
        product_markup = self.data["ktr_product"][product_id]["product_availability"]
        product_stocks = self.__get_stocks()
        product_prices = self.__get_prices()
        product_activity = self.__get_sale_channel_details()
        self.__print_specification(product_id,
                                   erp_code,
                                   product_code,
                                   product_name,
                                   product_flag,
                                   product_markup,
                                   product_stocks,
                                   product_prices,
                                   product_activity)

    @staticmethod
    def __print_specification(product_id,
                              erp_code,
                              product_code,
                              product_name,
                              product_flag,
                              product_markup,
                              product_stocks,
                              product_prices,
                              product_activity):
        print("TEST PRODUCT ATTRIBUTES: \n"
              f"Product DB id: {product_id} \n"
              f"ERP code: {erp_code} \n"
              f"Product code: {product_code} \n"
              f"Product name: {product_name} \n"
              f"Product flag: {product_flag} \n"
              f"Product markup: {product_markup} \n"
              f"Product stores availability: {product_stocks} \n"
              f"Product prices: {product_prices} \n"
              f"Product activity in sales channel: {product_activity} \n"
              )

    def __get_flag(self):
        """deserialize flag value from ktr_product_has_object_flag"""

        product_id = self.product_db_id
        dictionary = self.flags_dict
        data = self.data["ktr_product_has_object_flag"]

        try:
            product_flag = data[product_id]["object_flag_object_flag_id"]
        except KeyError:
            product_flag = "0"

        flag_code = dictionary[product_flag]
        return flag_code

    def __get_stocks(self):
        """deserialize stocks from ktr_warehouse_balance"""

        product_id = self.product_db_id
        dictionary = self.warehouse_dict
        data = self.data["ktr_warehouse_balance"]

        try:
            warehouse_raw = data[product_id]
            warehouse_ids = list(warehouse_raw.keys())
            stocks = ""
            for warehouse in range(len(warehouse_ids)):
                _id = warehouse_ids[warehouse]
                warehouse_name = dictionary[_id]
                warehouse_stock = "\n\t{:30} -> {} pcs.".format(warehouse_name,
                                                                warehouse_raw[_id]["`warehouse_balance_balance`"])
                stocks = stocks + warehouse_stock
            return stocks
        except KeyError:
            return "Stock unavailable"

    def __get_prices(self):
        """deserialize stocks from ktr_price"""

        product_id = self.product_db_id
        dictionary = self.price_dict
        data = self.data["ktr_price"]

        try:
            prices_raw = data[product_id]
            price_categories = list(prices_raw.keys())
            prices = ""
            for price_category in range(len(price_categories)):
                _id = price_categories[price_category]
                price_category_name = dictionary[_id]
                price = "\n\t{:30} -> brutto = {:20} netto = {:20} tax = {:20}".format(price_category_name,
                                                                                       prices_raw[_id][
                                                                                           "`price_value_gross`"],
                                                                                       prices_raw[_id][
                                                                                           "`price_value_net`"],
                                                                                       prices_raw[_id][
                                                                                           "`price_tax_rate`"])
                prices = prices + price
            return prices
        except KeyError:
            return "Prices unavailable"

    def __get_sale_channel_details(self):
        """deserialize channel status and availability from ktr_product_sales_channel_data"""

        dictionary = self.channel_dict
        product_id = self.product_db_id
        active = self.data["ktr_product_sales_channel_data"][product_id]["product_sales_channel_data_active"]
        visible = self.data["ktr_product_sales_channel_data"][product_id]["product_sales_channel_data_visible"]
        buy_active = self.data["ktr_product_sales_channel_data"][product_id]["product_sales_channel_data_buy_active"]
        status = self.data["ktr_product_sales_channel_data"][product_id]["product_sales_channel_data_status_id"]

        active = dictionary["activity"][active]
        visible = dictionary["visibility"][visible]
        buy_active = dictionary["purchasable"][buy_active]
        try:
            status = dictionary["status"][status]
        except KeyError:
            status = "status not included in automatic tests"

        activity_statement = f"\n\t - product is {active} in sales channel"
        visibility_statement = f"\n\t - product is {visible} for client "
        purchasable_statement = f"\n\t - product is {buy_active} by client"
        status_statement = f"\n\t - availability status is '{status}'"
        final_statement = activity_statement + visibility_statement + purchasable_statement + status_statement

        return final_statement

    @staticmethod
    def __read_from_file(file_name):
        with open(file_name) as file:
            content = file.read()
        return content
