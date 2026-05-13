from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

pytestmark = [pytest.mark.e2e, pytest.mark.search]

_SUGGESTION_CASES = [
    pytest.param("samsung", True,  id="search_samsung_producer"),
    pytest.param("monitory", False, id="search_monitory_no_producer"),
]


@allure.feature("Wyszukiwanie — podpowiedzi")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("phrase,is_producer", _SUGGESTION_CASES)
@pytest.mark.scenario("Weryfikacja podpowiedzi wyszukiwarki (suggester)")
def test_search_suggestions(page, runtime_env, phrase, is_producer):
    """Weryfikuje, że suggester wyszukiwarki pokazuje:
    - sekcję produktów z max. 6 wynikami
    - jeśli fraza jest nazwą producenta: link do strony producenta zawierający frazę
      oraz nazwy produktów zawierające frazę

    Migracja z: SearchTestsNUXT/TestSearchSuggestions.py
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH).wait_loaded()

    search_bar = home.header.search_bar
    search_bar.fill_phrase(phrase)
    search_bar.wait_for_suggestions()
    search_bar.expect_suggestion_products_section_visible()

    product_count = search_bar.get_suggestion_product_count()
    assert product_count <= 6, (
        f"Suggester wyświetla {product_count} produktów — oczekiwano co najwyżej 6."
    )
    assert product_count > 0, (
        f"Suggester nie wyświetla żadnych produktów dla frazy '{phrase}'."
    )

    if is_producer:
        product_names = search_bar.get_suggestion_product_names()
        for name in product_names:
            assert phrase.lower() in name.lower(), (
                f"Nazwa produktu '{name}' nie zawiera frazy '{phrase}'."
            )

        assert search_bar.has_producer_section(), (
            f"Brak sekcji producenta w suggesterze dla frazy '{phrase}'."
        )
        producer_href = search_bar.get_producer_link_href()
        assert phrase.lower() in producer_href.lower(), (
            f"Link producenta '{producer_href}' nie zawiera frazy '{phrase}'."
        )
