from TestCases.NetCornerProducts.Common.PageLocators.CommonHeaderLocators import (
    CommonSearchLocators,
)


class HeaderLocators:
    CONTAINER_header = "//div[@class='relative']//div[contains(@class, 'duration-300 lg')]"

    ELEMENT_logo = "//img[contains(@alt, 'Komputronik Logo')]"
    ELEMENT_your_account = "//span[contains(text(), 'Twoje konto')]"
    ELEMENT_login = "//div[@data-name='loginDialogTrigger']"  # develop branch
    ELEMENT_cart = CONTAINER_header + "//span[contains(text(), 'Koszyk')]"
    ELEMENT_cart_quantity = "//*[@data-name='cartLengthCounter']/div"
    ELEMENT_help_and_contact = CONTAINER_header + "//span[contains(text(), 'pomoc')]"
    ELEMENT_phone_number = "//span[contains(text(), '+48 61 668 00 07')]"
    ELEMENT_search_where = "//div[contains(@data-name, 'searchCategoryWrapper')]"

    ELEMENT_search_where_current_selected_category = ELEMENT_search_where + "//div//div"
    LIST_search_where = ELEMENT_search_where + "//div//div[not(contains(text(), 'wszędzie'))]"

    LINK_help_hover = "//div[contains(@class, 'overflow-hidden absolute')]"
    LINK_find_store = "//a[contains(text(), 'Salony')]"
    LINK_find_contact = "//a[contains(text(), 'Kontakt')]"
    LINK_find_complaint = "//a[contains(text(), 'Reklamacje')]"
    LINK_find_return = "//a[contains(text(), 'Zwroty')]"
    LINK_find_shipping = "//a[contains(text(), 'Dostawa')]"
    LINK_cart = "//span[contains(text(), 'Koszyk')]"

    DROP_DOWN_lvl_zero = "//ul[contains(@data-categories-lvl, '0')]"
    DROP_DOWN_all_elements = DROP_DOWN_lvl_zero + "//li"

    BUTTON_logout = "//button[contains(text(), 'Wyloguj')]"


class SearchLocators(CommonSearchLocators):
    INPUT_search = "//div[contains(@data-role, 'search')]//input[contains(@class, 'placeholder')]"
    BUTTON_search = "//button[contains(@type, 'submit')]"
    SECTION_products = "//div[@data-name='searchComponentResults']//div[contains(text(), 'Produkty')]"
    ELEMENTS_products = "//div[@data-name='searchComponentResults']//following-sibling::a[contains(@href, 'product')]"
    SECTION_producer = "//div[@data-name='searchComponentResults']//div[contains(text(), 'Produkty')]"
    ELEMENT_producer = "//div[@data-name='searchComponentResults']//following-sibling::a[contains(@href, 'producer')]"
    DROPDOWN_search_category = "//div[@data-name='searchCategoryWrapper']//i"
    SELECT_search_category = "//*[@data-name='searchCategories']/div[contains(text(), '{category}')]"
