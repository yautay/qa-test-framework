from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

pytestmark = [pytest.mark.e2e, pytest.mark.layout]


@allure.feature("Layout")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Weryfikacja elementów strukturalnych stopki")
def test_footer_elements(page, runtime_env):
    """Weryfikuje widoczność kluczowych elementów stopki:
    - obszar kontaktowy (link tel:)
    - sekcja social media z ikonami (Facebook, Instagram, YouTube, X, TikTok)
    - cztery sekcje linków: Zakupy, Obsługa klienta, Informacje, Komputronik S.A
    - obecność linków nawigacyjnych w stopce

    Migracja z: LayoutElementsTestsNUXT/TestFooterElements.py
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH)
    home.wait_loaded()

    home.footer.assert_visible()
    home.footer.expect_contact_area_visible()
    home.footer.expect_social_section_visible()
    home.footer.expect_all_social_links_visible()
    home.footer.expect_information_section_visible()
    home.footer.expect_client_service_section_visible()
    home.footer.expect_shopping_section_visible()
    home.footer.expect_about_us_section_visible()
    home.footer.expect_footer_links_present(min_count=4)
