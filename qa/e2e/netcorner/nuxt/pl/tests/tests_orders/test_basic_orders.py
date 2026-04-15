from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import auth_session_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import (
    ClientDataBuilder,
    auth_session_cases,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_aviable_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.orders]


@allure.feature("Proces zakupowy")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Podstawowy proces zakupowy - wysyłka kurierem")
def test_basic_orders(page, context, runtime_env, auth_case: AuthSessionCase):
    _prepare_client_session(page, context, runtime_env, auth_case)
    SelectProductWrappers(page, context, runtime_env).select_test_product(first_aviable_laptop_case())

def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase) -> bool:
    if not auth_case.authenticated:
        return False

    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany."
    )
    return True


