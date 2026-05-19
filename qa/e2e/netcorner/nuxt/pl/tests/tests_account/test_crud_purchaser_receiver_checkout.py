from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("CRUD nabywcy i odbiorcy w checkout — smoke alfa")
def test_crud_purchaser_receiver_checkout(page, context, runtime_env):
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Nie udało się przygotować zalogowanej sesji klienta do testu checkout CRUD."
    )

    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(first_available_laptop_case())
    assert selected is not None, "Nie udało się dodać produktu przed testem checkout CRUD."
    CartAndCheckoutWrappers(page, context, runtime_env).process_cart()
    checkout = CheckoutPage(page, runtime_env.base_url).wait_loaded()

    # Krok 1: kurier
    checkout.content.delivery_type.click_courier_tile()

    # Krok 2: overlay odbiorcy — wypełnienie danych
    checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
    receiver_overlay = Overlays(page).checkout_courier_receiver.wait_visible()
    receiver_overlay.fill_receiver_data(private_person_delivery_courier_receiver())
    receiver_overlay.click_add_details()
    receiver_overlay.wait_hidden(timeout=10_000)

    # Krok 3: sekcja formy dostawy widoczna
    delivery_section = page.locator("[data-picker='delivery']").first
    assert delivery_section.is_visible(), (
        "Sekcja 'Wybierz formę dostawy' (krok 3) nie jest widoczna po wypełnieniu danych odbiorcy."
    )

    # Krok 4: sekcja nabywcy widoczna w DOM
    purchaser_section = page.locator("[data-picker='purchaser']").first
    assert purchaser_section.is_visible(), (
        "Sekcja 'Podaj dane do zakupu' (krok 4) nie jest widoczna na checkoucie."
    )
    # TODO: weryfikacja wypełnienia danych nabywcy + BLIK wymaga działającego delivery API (krok 3)
    # Na galak.test delivery methods zwracają błąd API — purchaser pozostaje w stanie awaiting.
    _ = private_person_checkout_purchaser()  # dane przygotowane, do użycia gdy API będzie działać
