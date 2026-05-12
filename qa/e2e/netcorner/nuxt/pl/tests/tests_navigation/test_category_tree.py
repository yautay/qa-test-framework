from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.layout]

# ---------------------------------------------------------------------------
# Test data: mirrors data_category_tree.py from Selenium suite.
# Each entry: (root, first_lvl, second_lvl | None, third_lvl | None)
# In the current NUXT megamenu DOM:
#   - first_lvl is a level-1 item (ul[data-categories-lvl='1'] li a)
#   - second_lvl and third_lvl are level-2 items inside the first_lvl panel
# ---------------------------------------------------------------------------
_ONE_LEVEL_CASES = [
    pytest.param("RTV",                    "Telewizory",              None,          None, id="one_level_rtv_telewizory"),
    pytest.param("Laptopy i komputery",    "Laptopy",                 None,          None, id="one_level_laptopy"),
    pytest.param("Telefony i Smartwatche", "Telefony i Smartfony",    None,          None, id="one_level_telefony"),
]

_TWO_LEVEL_CASES = [
    pytest.param("Sprzęt PC", "Peryferia PC", "Klawiatury",    None, id="two_levels_peryferia_klawiatury"),
    pytest.param("Sprzęt PC", "Peryferia PC", "Monitory",      None, id="two_levels_peryferia_monitory"),
    pytest.param("Sprzęt PC", "Części PC",    "Karty graficzne", None, id="two_levels_czesci_gpu"),
]

_THREE_LEVEL_CASES = [
    pytest.param("Sprzęt PC", "Sieci i komunikacja", "Monitoring",               "Kamery do monitoringu",         id="three_levels_monitoring_kamery"),
    pytest.param("Sprzęt PC", "Oprogramowanie",      "Programy biurowe",         "Microsoft Office",              id="three_levels_ms_office"),
    pytest.param("Sprzęt PC", "Części PC",           "Chłodzenie",               "Wentylatory do komputerów",     id="three_levels_chlodzenie_wentylatory"),
]

# URLs excluded from product listing assertion (known non-listing pages)
_EXCLUDED_URL_FRAGMENTS = ("laptop-dla-nauczyciela", "advanced-configurator")


def _verify_link_has_listing(page, base_url: str, href: str) -> None:
    """Navigate to href and assert the product listing is visible."""
    path = href.lstrip("/")
    listing = ListingPage(page, base_url)
    listing.open(path).wait_loaded()
    count = listing.content.content.count()
    assert count > 0, f"URL '{href}' nie zawiera produktów na listingu."


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

    # 1. Collect level-2 links for the first_lvl tile
    level2_links = nav.get_level2_links_for(root, first_lvl)
    assert level2_links, (
        f"Megamenu '{root} > {first_lvl}' nie zawiera żadnych linków poziomu 2."
    )

    if second_lvl is None:
        # One-level case: verify a representative sample of level-2 links
        sample = [
            href for href in level2_links
            if not any(ex in href for ex in _EXCLUDED_URL_FRAGMENTS)
        ][:3]  # visit up to 3 links to keep test fast
        for href in sample:
            _verify_link_has_listing(page, base_url, href)
        return

    # Two/three-level: navigate to second_lvl link
    second_href = next(
        (h for h in level2_links if second_lvl.lower() in h.lower()),
        None,
    )
    assert second_href is not None, (
        f"Nie znaleziono linku dla '{second_lvl}' w megamenu '{root} > {first_lvl}'."
    )
    if not any(ex in second_href for ex in _EXCLUDED_URL_FRAGMENTS):
        _verify_link_has_listing(page, base_url, second_href)

    if third_lvl is None:
        return

    # Three-level: navigate to third_lvl link (also a level-2 link in current DOM)
    third_href = next(
        (h for h in level2_links if third_lvl.lower() in h.lower()),
        None,
    )
    assert third_href is not None, (
        f"Nie znaleziono linku dla '{third_lvl}' w megamenu '{root} > {first_lvl}'."
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
    panelu megamenu dla 'first_lvl'.

    Migracja z: CategoryTreeTestsNUXT/TestCategoryTree.py — test_category_tree_three_levels
    """
    _run_category_tree_case(page, runtime_env, root, first_lvl, second_lvl, third_lvl)
