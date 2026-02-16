from TestCases.NetCornerProducts.Common.PageLocators.CommonProductListLocators import (
    CommonProductListLocators,
)


class FilterLocators:
    ELEMENTS_unroll_all_filters = "//div[contains(text(), 'Pokaż więcej ')]"
    CONTAINER_filter_type = "//div[contains(@data-group-key, '{filter_data_type}')]"
    INPUT_checkbox = "//input/following-sibling::span[contains(., '{filter_value}')]"
    INPUT_number = "//input[@type='number']"
    CONTAINER_active_filters = "//div[@data-role='filters']/child::div[not(@data-name='filtersWrapper')]"
    ELEMENTS_active_filters = CONTAINER_active_filters + "//div/span[contains(@class, 'bold')]"


class ProductListLocators(CommonProductListLocators):
    ELEMENTS_products_url = "//div[contains(@data-name, 'listingContent')]//a[contains(@href, '/product/') or contains(@href, '/p/')]"
    CONTAINER_products_list = "//div[contains(@data-name, 'listingContent')]"
    ELEMENT_checkbox_show_unavailable = "//input[@id='checkboxShowUnavailable']"
    MAIN_CONTAINER_product_list = "//div[@id='pageContent']"
    BUTTONS_add_to_cart = "//div[contains(@class, 'border-transparent')]//div[contains(@class, 'self-end')]//button"
    DROPDOWN_sorting_menu = "//div[contains(@class, 'relative cursor-pointer')]"
    BUTTON_sort_option = DROPDOWN_sorting_menu + "//div[contains(@class, 'items') and text()='{}']"
    ELEMENT_product_price = "//div[@class='prices']/span"
    ELEMENT_product_name = "//div[@data-name='listingContent']//h2"
    BUTTONS_add_to_compare = "//span[contains(text(), 'orówna')]"
    ELEMENT_products_count = "//h1/following-sibling::span"
    ELEMENT_next_pagination_page = "//a[@aria-label='nawiguj do następnej strony']"
    ELEMENT_product_webelement_link = "//div[contains(@data-name, 'listingContent')]//a[@href]"
    ELEMENTS_products_by_attribute = "//div[contains(text(), '{attribute}' )]/ancestor::div[contains(@data-name, 'listingTile')]//h2"
    ELEMENTS_products_with_public_code = "//div[contains(text(), 'Cena z kodem:')]/ancestor::div[@data-name='listingTile']//h2"
    ELEMENTS_erp_codes = "//p[contains(., 'Kod systemowy')]"
