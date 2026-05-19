from __future__ import annotations

import re

import allure
import pytest

from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import AdminCategorySearchKeywordsPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_search]


@allure.feature("Wyszukiwanie")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Frazy wyjątków searcha kierują na przypisaną kategorię")
def test_simple_search_exceptions(page, runtime_env, admin_panel):
    admin_panel.open_admin()
    entries = AdminCategorySearchKeywordsPage(page, admin_panel.admin_env.base_url).navigate_to().get_entries(limit=5)
    assert entries, "Admin nie zwrócił żadnych fraz wyszukiwania kategorii do testu wyjątków searcha."

    home = HomePage(page, runtime_env.base_url)
    for entry in entries:
        for phrase in entry.phrases[:2]:
            home.open(HomePage.PATH).wait_loaded()
            home.header.search_bar.fill_phrase(phrase)
            home.header.search_bar.submit()
            page.wait_for_url(re.compile(r".*/category/\d+/.*"), timeout=10_000)
            assert f"/category/{entry.category_id}" in page.url, (
                f"Fraza '{phrase}' powinna kierować do kategorii '{entry.category_id}' ({entry.category_name}), "
                f"ale finalny URL to '{page.url}'."
            )
