from __future__ import annotations

import pytest
import allure

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core]

# Stałe produkty testowe ad-hoc na środowisku galak.test.
# Zestaw Alfa i Delta mają pełny status dostępności; Bravo i Charlie nie mają statusu (NO_STATUS).
_ADHOC_PRODUCTS = [
    pytest.param(
        "/product/500001006/-test-product-ad-hoc-zestaw-alfa.html",
        "ALFA",
        True,
        id="adhoc_alfa",
    ),
    pytest.param(
        "/product/500001007/-test-product-ad-hoc-zestaw-bravo.html",
        "BRAVO",
        False,
        id="adhoc_bravo",
    ),
    pytest.param(
        "/product/500001008/-test-product-ad-hoc-zestaw-charlie.html",
        "CHARLIE",
        False,
        id="adhoc_charlie",
    ),
    pytest.param(
        "/product/500001009/-test-product-ad-hoc-zestaw-delta.html",
        "DELTA",
        True,
        id="adhoc_delta",
    ),
]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Karta produktu ad-hoc — ładuje się i pokazuje kluczowe dane")
@pytest.mark.parametrize("path,label,has_status", _ADHOC_PRODUCTS, ids=lambda p: p if isinstance(p, str) else None)
def test_adhoc_product_page_loads(page, runtime_env, path, label, has_status):
    product = ProductPage(page, runtime_env.base_url).open(path).wait_loaded()

    data = product.content.price.get_data()

    assert data.final_price, f"Produkt {label}: brak ceny końcowej na stronie."

    if has_status:
        assert data.availability_status is not None, (
            f"Produkt {label}: oczekiwano statusu dostępności, ale go nie znaleziono."
        )
    else:
        # Produkty NO_STATUS nie mają elementu statusAvailable w DOM — brak asercji statusu.
        pass
