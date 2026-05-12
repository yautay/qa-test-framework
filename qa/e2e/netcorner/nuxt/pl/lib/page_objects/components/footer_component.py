from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class FooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="footer"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Footer Component")

        # layout locators — all scoped inside [data-name='footer']
        self.__contact_tel = self.find("a[href^='tel:']")
        self.__social_heading = self.find("div.font-bold:has-text('Znajdziesz nas na:')")
        self.__social_facebook = self.find("i.i-facebook-outline")
        self.__social_instagram = self.find("i.i-instagram")
        self.__social_youtube = self.find("i.i-youtube")
        self.__social_x = self.find("i.i-x")
        self.__social_tiktok = self.find("i.i-tiktok")

        # footer content section (4 link-columns)
        self.__footer_content = self.find("section[data-name='footerContent']")
        self.__section_shopping = self.__footer_content.locator("div.font-semibold:has-text('Zakupy')")
        self.__section_client_service = self.__footer_content.locator("div.font-semibold:has-text('Obsługa klienta')")
        self.__section_information = self.__footer_content.locator("div.font-semibold:has-text('Informacje')")
        self.__section_about_us = self.__footer_content.locator("div.font-semibold:has-text('Komputronik S.A')")
        self.__footer_links = self.__footer_content.locator("li a")

    # --- layout assertions ---

    @step("Sprawdzam widoczność obszaru kontaktowego (tel)")
    def expect_contact_area_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__contact_tel).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność nagłówka sekcji social media")
    def expect_social_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__social_heading).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność ikon social media (Facebook, Instagram, YouTube, X, TikTok)")
    def expect_all_social_links_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__social_facebook).to_be_visible(timeout=timeout_ms)
        expect(self.__social_instagram).to_be_visible(timeout=timeout_ms)
        expect(self.__social_youtube).to_be_visible(timeout=timeout_ms)
        expect(self.__social_x).to_be_visible(timeout=timeout_ms)
        expect(self.__social_tiktok).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji 'Informacje'")
    def expect_information_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__section_information).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji 'Obsługa klienta'")
    def expect_client_service_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__section_client_service).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji 'Zakupy'")
    def expect_shopping_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__section_shopping).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji 'Komputronik S.A'")
    def expect_about_us_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__section_about_us).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam, że stopka zawiera linki nawigacyjne")
    def expect_footer_links_present(self, min_count: int = 1) -> Self:
        count = self.__footer_links.count()
        assert count >= min_count, f"Oczekiwano co najmniej {min_count} linków w stopce, znaleziono: {count}"
        return self


class CartFooterComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="cartFooter"], [data-name="stickyBar"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Cart Footer Component")

        self.__btn_continue = self.root.get_by_role("button", name="Przejdź dalej").first
        self.__btn_clear_cart = self.root.get_by_role("button", name="Wyczyść koszyk").first
        self.__btn_back_to_shopping = self.root.get_by_role("button", name="Wróć do zakupów").first
        self.__btn_copy_link = self.root.get_by_text("Skopiuj link").first

    # actions
    @step("Klikam 'Przejdź dalej'")
    def click_continue(self) -> None:
        self.pointer_click(self.__btn_continue)

    @step("Klikam 'Wyczyść koszyk'")
    def click_clear_cart(self) -> None:
        self.pointer_click(self.__btn_clear_cart)

    @step("Klikam 'Wróć do zakupów'")
    def click_back_to_shopping(self) -> None:
        self.pointer_click(self.__btn_back_to_shopping)

    @step("Klikam 'Skopiuj link'")
    def click_copy_link(self) -> None:
        self.pointer_click(self.__btn_copy_link)
