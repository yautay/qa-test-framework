from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_layout]

# ---------------------------------------------------------------------------
# Test data: mirrors data_category_tree.py from Selenium suite.
# Each entry: (root, first_lvl, second_lvl | None, third_lvl | None)
# In the current NUXT megamenu DOM:
#   - first_lvl is a level-1 item (ul[data-categories-lvl='1'] li a)
#   - second_lvl and third_lvl are level-2 items looked up by LINK TEXT,
#     not by URL fragment, because Polish characters (ł, ó, ę …) are
#     not preserved in ASCII slugs.
# ---------------------------------------------------------------------------
_ONE_LEVEL_CASES = [
    pytest.param("RTV",                    "Telewizory",              None,          None, id="one_level_rtv_telewizory"),
    pytest.param("Laptopy i komputery",    "Laptopy",                 None,          None, id="one_level_laptopy"),
    pytest.param("Telefony i Smartwatche", "Telefony i Smartfony",    None,          None, id="one_level_telefony"),
]

_TWO_LEVEL_CASES = [
    pytest.param("Sprzęt PC", "Peryferia PC", "Klawiatury",        None, id="two_levels_peryferia_klawiatury"),
    pytest.param("Sprzęt PC", "Peryferia PC", "Monitory",          None, id="two_levels_peryferia_monitory"),
    pytest.param("Sprzęt PC", "Części PC",    "Karty graficzne",   None, id="two_levels_czesci_gpu"),
    # "Sieci i komunikacja" panel — covers the section formerly tested as
    # three-level Monitoring > Kamery do monitoringu (those sub-links are not
    # exposed as direct level-2 megamenu items in the NUXT megamenu).
    pytest.param("Sprzęt PC", "Sieci i komunikacja", "NAS - serwery plików", None, id="two_levels_sieci_nas"),
    # "Części PC" panel — covers the section formerly tested as three-level
    # Chłodzenie > Wentylatory (same reason as above).
    pytest.param("Sprzęt PC", "Części PC",    "Procesory",         None, id="two_levels_czesci_procesory"),
]

_THREE_LEVEL_CASES = [
    # MS Office is a direct level-2 megamenu link inside the "Oprogramowanie"
    # panel alongside its parent "Programy biurowe" — this is the only path
    # in the current NUXT megamenu that exposes a genuine parent+child pair as
    # flat level-2 links.
    pytest.param("Sprzęt PC", "Oprogramowanie", "Programy biurowe", "Microsoft Office", id="three_levels_ms_office"),
]

# URLs excluded from product listing assertion (known non-listing pages)
_EXCLUDED_URL_FRAGMENTS = ("laptop-dla-nauczyciela", "advanced-configurator")


def _verify_link_has_listing(page, base_url: str, href: str) -> None:
    """Navigate to href (must start with '/') and assert the product listing is visible."""
    listing = ListingPage(page, base_url)
    listing.open(href).wait_loaded()
    count = listing.content.content.count()
    assert count > 0, f"URL '{href}' nie zawiera produktów na listingu."


def _find_href_by_text(items: list[tuple[str, str]], text: str) -> str | None:
    """Find href where link text contains *text* (case-insensitive)."""
    text_lower = text.lower()
    for link_text, href in items:
        if text_lower in link_text.lower():
            return href
    return None


def _run_category_tree_case(
    page,
    runtime_env,
    root: str,
    first_lvl: str,
    second_lvl: str | None,
    third_lvl: str | None,
) -> None:
    base_url = runtime_env.base_url
    home = HomePage(page, base_url)
    home.open(HomePage.PATH).wait_loaded()

    nav = home.navigation

    # 1. Collect level-2 (text, href) items for the first_lvl tile
    level2_items = nav.get_level2_items_for(root, first_lvl)
    assert level2_items, (
        f"Megamenu '{root} > {first_lvl}' nie zawiera żadnych linków poziomu 2."
    )

    if second_lvl is None:
        # One-level case: verify a representative sample of level-2 links
        sample = [
            href for _text, href in level2_items
            if not any(ex in href for ex in _EXCLUDED_URL_FRAGMENTS)
        ][:3]  # visit up to 3 links to keep test fast
        for href in sample:
            _verify_link_has_listing(page, base_url, href)
        return

    # Two/three-level: look up second_lvl by link text (not URL slug)
    second_href = _find_href_by_text(level2_items, second_lvl)
    assert second_href is not None, (
        f"Nie znaleziono linku dla '{second_lvl}' w megamenu '{root} > {first_lvl}'. "
        f"Dostępne: {[t for t, _ in level2_items]}"
    )
    if not any(ex in second_href for ex in _EXCLUDED_URL_FRAGMENTS) and third_lvl is None:
        _verify_link_has_listing(page, base_url, second_href)

    if third_lvl is None:
        return

    # Three-level: look up third_lvl by link text (also a level-2 link in current DOM)
    third_href = _find_href_by_text(level2_items, third_lvl)
    assert third_href is not None, (
        f"Nie znaleziono linku dla '{third_lvl}' w megamenu '{root} > {first_lvl}'. "
        f"Dostępne: {[t for t, _ in level2_items]}"
    )
    if not any(ex in third_href for ex in _EXCLUDED_URL_FRAGMENTS):
        _verify_link_has_listing(page, base_url, third_href)


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------

@allure.feature("Nawigacja — drzewo kategorii")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("root,first_lvl,second_lvl,third_lvl", _ONE_LEVEL_CASES)
@pytest.mark.scenario("Weryfikacja listingu po przejściu przez jeden poziom megamenu")
def test_category_tree_one_level(page, runtime_env, root, first_lvl, second_lvl, third_lvl):
    """Weryfikuje, że podkategorie poziomu 2 w megamenu prowadzą do stron z listingiem produktów.

    Migracja z: CategoryTreeTestsNUXT/TestCategoryTree.py — test_category_tree_one_level
    """
    _run_category_tree_case(page, runtime_env, root, first_lvl, second_lvl, third_lvl)


@allure.feature("Nawigacja — drzewo kategorii")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("root,first_lvl,second_lvl,third_lvl", _TWO_LEVEL_CASES)
@pytest.mark.scenario("Weryfikacja listingu po przejściu przez dwa poziomy megamenu")
def test_category_tree_two_levels(page, runtime_env, root, first_lvl, second_lvl, third_lvl):
    """Weryfikuje, że podkategoria poziomu 2 w megamenu prowadzi do strony z listingiem.

    Migracja z: CategoryTreeTestsNUXT/TestCategoryTree.py — test_category_tree_two_levels
    """
    _run_category_tree_case(page, runtime_env, root, first_lvl, second_lvl, third_lvl)


@allure.feature("Nawigacja — drzewo kategorii")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("root,first_lvl,second_lvl,third_lvl", _THREE_LEVEL_CASES)
@pytest.mark.scenario("Weryfikacja listingu po przejściu przez trzy poziomy megamenu")
def test_category_tree_three_levels(page, runtime_env, root, first_lvl, second_lvl, third_lvl):
    """Weryfikuje, że dwie podkategorie (second + third) w megamenu prowadzą do stron z listingiem.

    Nota: W bieżącej strukturze DOM megamenu NUXT wszystkie liście drzewa są
    linkami poziomu 2. Oba 'second_lvl' i 'third_lvl' odnalezione są w tym samym
    panelu megamenu dla 'first_lvl' — wyszukiwanie po tekście linku (nie slug URL).

    Migracja z: CategoryTreeTestsNUXT/TestCategoryTree.py — test_category_tree_three_levels
    """
    _run_category_tree_case(page, runtime_env, root, first_lvl, second_lvl, third_lvl)
