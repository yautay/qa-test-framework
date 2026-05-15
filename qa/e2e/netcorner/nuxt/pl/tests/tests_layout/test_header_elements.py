from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

pytestmark = [pytest.mark.e2e, pytest.mark.layout]


@allure.feature("Layout")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Weryfikacja elementów strukturalnych nagłówka strony")
def test_header_elements(page, runtime_env):
    """Weryfikuje widoczność kluczowych elementów nagłówka:
    - logo sklepu
    - pasek wyszukiwania
    - przyciski akcji (login, koszyk)
    - link Kontakt i pomoc
    - pasek kategorii poziomu 0 (navigationBar)

    Migracja z: LayoutElementsTestsNUXT/TestHeaderElements.py → test_header_elements
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH)
    home.wait_loaded()

    home.header.expect_logo_visible()
    home.header.search_bar.assert_visible()
    home.header.actions.assert_visible()
    home.header.expect_help_contact_visible()
    home.navigation.expect_categories_bar_visible()


@allure.feature("Layout")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Weryfikacja dropdownu wyszukiwania 'gdzie szukasz'")
def test_search_where_dropdown(page, runtime_env):
    """Weryfikuje dropdown wyboru kategorii wyszukiwania:
    - domyślna wartość to 'wszędzie'
    - po kliknięciu wyświetla opcje kategorii

    Migracja z: LayoutElementsTestsNUXT/TestHeaderElements.py → test_search_where_dropdown_menu
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH)
    home.wait_loaded()

    home.header.expect_search_where_visible()
    home.header.assert_search_where_default()
    home.header.expect_search_where_has_options()
