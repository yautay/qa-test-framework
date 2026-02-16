class FooterLocators:
    CONTAINER_footer = "//footer"
    CONTAINER_links_social = "//div[contains(text(), 'Znajdziesz nas')]"

    LINK_info_line = CONTAINER_footer + "//div[contains(@class, 'items')]//parent::a[contains(@href, '07')]"
    LINK_contact = CONTAINER_footer + "//div[contains(@class, 'items')]"
    LINK_facebook = "//i[contains(@class, 'i-facebook-outline')]/parent::a"
    LINK_instagram = "//i[contains(@class, 'i-instagram')]/parent::a"
    LINK_youtube = "//i[contains(@class, 'i-youtube')]/parent::a"
    LINK_x = "//i[contains(@class, 'i-x')]/parent::a"
    LINK_tiktok = "//i[contains(@class, 'i-tiktok')]/parent::a"

    SECTION_information = "//div[contains(text(), 'Informacje')]//parent::div"
    LIST_information_elements = SECTION_information + "//parent::div//ul/li/a"

    SECTION_client_service = "//div[contains(text(), 'Obsługa klienta')]//parent::div"
    LIST_client_service_elements = SECTION_client_service + "//parent::div//ul/li/a"

    SECTION_shopping = "//div[contains(text(), 'Zakupy')]//parent::div"
    LIST_shopping_elements = SECTION_shopping + "//parent::div//ul/li/a"

    SECTION_about_us = "//div[contains(text(), 'Komputronik')]//parent::div"
    LIST_about_us_elements = SECTION_about_us + "//parent::div//ul/li/a"
