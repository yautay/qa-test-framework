from TestCases.NetCornerProducts.Common.PageObjects.CommonFooterPageObject import (
    CommonFooterPageObject,
)

import settings

from ..PageLocators import FooterLocators


class FooterObjects(CommonFooterPageObject):
    def __init__(self, driver, check_twin_dictionaries: CommonFooterPageObject.AnyCommon | None = None):
        super().__init__(driver)

        self._are_dictionaries_identical = check_twin_dictionaries
        self.locator = FooterLocators()

    def verify_footer_elements(self, phone_number: str):
        self.wait_for.element_visible(self.locator.CONTAINER_footer, "Footer container is not visible!")
        self.wait_for.element_visible(self.locator.LINK_contact, "Contact link is not visible!")
        infoline = self.wait_for.element_visible(self.locator.LINK_info_line, "Infoline link is not visible!")
        assert infoline.text == phone_number, "Not expected text for infoline element."

    def assert_information_section(self, url: str, information_items: dict):
        full_urls = self._assert_footer_sections(url, information_items)
        self.assert_section(
            section_locator=self.locator.SECTION_information,
            list_locator=self.locator.LIST_information_elements,
            items_function=self.information_items,
            url=full_urls,
            error_message="Information list is not visible!",
            check_twin_dirs=self._are_dictionaries_identical
        )

    def assert_client_service_section(self, url: str, client_service_items: dict):
        full_urls = self._assert_footer_sections(url, client_service_items)
        self.assert_section(
            section_locator=self.locator.SECTION_client_service,
            list_locator=self.locator.LIST_client_service_elements,
            items_function=self.client_service_items,
            url=full_urls,
            error_message="Client service section is not visible!",
            check_twin_dirs=self._are_dictionaries_identical
        )

    def assert_shopping_section(self, url: str, shopping_items: dict):
        full_urls = self._assert_footer_sections(url, shopping_items)
        self.assert_section(
            section_locator=self.locator.SECTION_shopping,
            list_locator=self.locator.LIST_shopping_elements,
            items_function=self.shopping_items,
            url=full_urls,
            error_message="Shopping section is not visible!",
            check_twin_dirs=self._are_dictionaries_identical
        )

    def assert_about_us_section(self, url: str, about_us_items: dict):
        full_urls = self._assert_footer_sections(url, about_us_items)
        self.assert_section(
            section_locator=self.locator.SECTION_about_us,
            list_locator=self.locator.LIST_about_us_elements,
            items_function=self.about_us_items,
            url=full_urls,
            error_message="About Us section is not visible!",
            check_twin_dirs=self._are_dictionaries_identical
        )

    def verify_social_section_elements(self, social_platforms: dict):
        for platform in social_platforms:
            self.wait_for.element_visible(getattr(self.locator, f"LINK_{platform}"),
                                          f"{platform.capitalize()} icon and link are not visible!")

    def verify_attribute_social_section_elements(self, urls: dict):
        for platform, url in urls.items():
            self.element_attribute.attribute_has_value(getattr(self.locator, f"LINK_{platform}"), "href", url)

    @staticmethod
    def client_service_items(url: dict) -> dict:
        return url

    @staticmethod
    def about_us_items(url: dict) -> dict:
        extracted_domain = FooterObjects._extract_domain_name(url)
        div = f"{extracted_domain}".split("/")[-2:][0]

        if settings.server_type != "demo":
            url["Kariera"] = "https://wp-kariera-" + div + "/"
        if settings.server_type != "prod":
            del url["Biuro Prasowe"]

        return url

    @staticmethod
    def shopping_items(url: dict) -> dict:
        return url

    @staticmethod
    def information_items(url: dict) -> dict:
        extracted_domain = FooterObjects._extract_domain_name(url)
        div = f"{extracted_domain}".split("/")[-2:][0]
        div2 = f"{extracted_domain}".split("-")[-1:][0]

        if settings.server_type != "demo":
            url["Nano"] = "https://wp-nano-" + div + "/"
            url["Komputronik Gaming"] = "https://wp-komputronik-gaming-" + div2 + "/"

        return url
