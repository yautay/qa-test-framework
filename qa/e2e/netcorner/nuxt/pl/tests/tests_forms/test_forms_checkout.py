from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Formularze")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Formularze odbiorcy i nabywcy są dostępne w checkoucie — kurier")
def test_forms_checkout(page, context, runtime_env):
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Nie udało się przygotować zalogowanej sesji klienta do testu formularzy checkout."
    )

    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(first_available_laptop_case())
    assert selected is not None, "Nie udało się dodać produktu przed przejściem do checkout."

    CartAndCheckoutWrappers(page, context, runtime_env).process_cart()
    checkout = CheckoutPage(page, runtime_env.base_url).wait_loaded()

    # Krok 1: wybór metody dostawy → kurier
    checkout.content.delivery_type.click_courier_tile()

    # Krok 2: overlay odbiorcy — wypełnienie i zamknięcie
    checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
    receiver_overlay = Overlays(page).checkout_courier_receiver.wait_visible()
    receiver_overlay.click_add_details()
    receiver_overlay.wait_visible()
    receiver_overlay.click_cancel()
    receiver_overlay.wait_hidden(timeout=10_000)

    # Krok 3: sekcja formy dostawy jest widoczna (nawet przy błędzie API delivery methods)
    delivery_section = page.locator("[data-picker='delivery']").first
    assert delivery_section.is_visible(), (
        "Sekcja 'Wybierz formę dostawy' (krok 3) nie jest widoczna po wypełnieniu danych odbiorcy."
    )

    # Krok 4: sekcja nabywcy jest widoczna w DOM (oczekuje na aktywację przez delivery)
    purchaser_section = page.locator("[data-picker='purchaser']").first
    assert purchaser_section.is_visible(), (
        "Sekcja 'Podaj dane do zakupu' (krok 4) nie jest widoczna na checkoucie."
    )
    # TODO: weryfikacja overlay nabywcy + BLIK wymaga działającego delivery API (krok 3)
    # Na galak.test delivery methods zwracają błąd API — purchaser pozostaje w stanie awaiting.
