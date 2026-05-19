from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_layout]


@allure.feature("Layout")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Weryfikacja elementów strukturalnych strony głównej")
def test_homepage_elements(page, runtime_env):
    """Weryfikuje widoczność kluczowych sekcji strony głównej:
    - slider banerów z paginacją
    - sekcja produktów (dailyDeal)

    Migracja z: LayoutElementsTestsNUXT/TestHomePageElements.py
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH)
    home.wait_loaded()

    home.content.hero.expect_banners_visible()
    home.content.hero.expect_products_section_visible()
