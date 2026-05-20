from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

import allure
import pytest

import settings_cli
from framework.artifacts import RunArtifacts
from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import SortOptions
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import CheckoutDeliveryCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import checkout_delivery_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import (
    ClientDataBuilder,
    auth_session_cases_basic_orders,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import AvailabilityStatuses

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_smoke]

_SEARCH_PHRASE = "kabel sata"
_KNOWN_MIN_QTY_SYSTEM_CODES = {"500000510", "500000511"}
_PRODUCTION_ORDER_COMMENT = "Zamówienie testowe PiRO, proszę o anulowanie i nierealizowanie"


@pytest.fixture(scope="session")
def reusable_smoke_user_cache() -> dict[str, object]:
    return {}


def _smoke_order_cases() -> list[tuple[AuthSessionCase, CheckoutDeliveryCase]]:
    auth_cases = {case.case_id: case for case in auth_session_cases_basic_orders()}
    delivery_cases = {case.case_id: case for case in checkout_delivery_cases()}
    return [
        (auth_cases["logged_in"], delivery_cases["courier_service"]),
        (auth_cases["logged_in"], delivery_cases["store_pickup"]),
        (auth_cases["anonymous"], delivery_cases["dhl_pop"]),
        (auth_cases["anonymous"], delivery_cases["inpost"]),
        (auth_cases["registered_login_in_cart_overlay"], delivery_cases["courier_service"]),
        (auth_cases["registered_login_in_cart_overlay"], delivery_cases["dhl_pop"]),
    ]


@allure.feature("Proces zakupowy")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize(
    ("auth_case", "delivery_case"),
    _smoke_order_cases(),
    ids=[f"{auth_case.case_id}__{delivery_case.case_id}" for auth_case, delivery_case in _smoke_order_cases()],
)
@pytest.mark.scenario("Smoke proces zakupowy - auth x delivery (6 przypadków)")
def test_smoke_basic_orders(
    page,
    context,
    runtime_env,
    run_artifacts: RunArtifacts,
    auth_case: AuthSessionCase,
    delivery_case: CheckoutDeliveryCase,
    reusable_smoke_user_cache: dict[str, object],
):
    page.goto(runtime_env.base_url, wait_until="domcontentloaded")
    if runtime_env.server_name == "prod":
        context.add_cookies([{"name": "recaptcha_test", "value": "on", "url": runtime_env.base_url}])
        page.reload(wait_until="domcontentloaded")
    use_production_email = _use_production_email_for_case(auth_case, delivery_case, runtime_env)
    user_data = _prepare_client_session(
        page,
        context,
        runtime_env,
        auth_case,
        use_production_email=use_production_email,
        reusable_smoke_user_cache=reusable_smoke_user_cache,
    )
    selected_product_data = _select_search_product_for_smoke(page, runtime_env)
    assert selected_product_data.product_page_data is not None, "Produkt nie został dodany do koszyka."

    effective_delivery_case = _prepare_checkout_case(
        delivery_case,
        comment=_PRODUCTION_ORDER_COMMENT,
        forced_email=settings_cli.production_test_email if use_production_email else None,
    )

    dump_data(
        auth_case=auth_case,
        delivery_case=delivery_case,
        user_data=user_data,
        product=selected_product_data.product,
    )

    listing_data = selected_product_data.listing_data
    product_page_data = selected_product_data.product_page_data

    assert product_page_data.availability_status == listing_data.shipping_status, (
        f"Oczekiwany status dostępności produktu '{listing_data.shipping_status}' "
        f"różni się od tego wyświetlanego na stronie '{product_page_data.availability_status}'."
    )
    assert product_page_data.final_price == listing_data.final_price, (
        f"Oczekiwana cena produktu '{listing_data.final_price}' "
        f"różni się od tej wyświetlanej na stronie '{product_page_data.final_price}'."
    )

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart(continue_without_login=not auth_case.login_in_cart_overlay)
    if auth_case.login_in_cart_overlay:
        assert user_data is not None, "Brak danych zarejestrowanego klienta do logowania w koszyku."
        Overlays(page).login.wait_visible().log_client(user_data.email, user_data.password)

    checkout_process_data = checkout_wrappers.process_checkout(
        effective_delivery_case.delivery_type,
        effective_delivery_case.delivery_objects,
        effective_delivery_case.purchaser_objects,
        effective_delivery_case.payment_objects,
    )
    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    total_to_pay = (checkout_process_data.typ_summary_data.total_to_pay or "").strip()
    assert order_number, (
        "Nie udało się potwierdzić złożenia zamówienia: brak numeru zamówienia w podsumowaniu."
    )
    _append_production_order_log(
        run_artifacts,
        sales_channel="PL",
        order_number=order_number,
        total_to_pay=total_to_pay,
    )


def _select_search_product_for_smoke(page, runtime_env) -> SelectProductData:
    excluded_system_codes = set(_KNOWN_MIN_QTY_SYSTEM_CODES)
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH).wait_loaded()
    home.header.search_bar.fill_phrase(_SEARCH_PHRASE)
    home.header.search_bar.submit()

    listing_page = ListingPage(page, runtime_env.base_url).wait_loaded()
    listing_page.content.sorting.select_sort_option(SortOptions.PRICE_ASC)

    result = listing_page.open_first_product_by_shipping_status_excluding_system_codes(
        AvailabilityStatuses.ONE_DAY,
        excluded_system_codes,
        skip_min_qty_gt_one=True,
    )
    assert result is not None, (
        "Nie znaleziono produktu z wyszukiwarki 'kabel sata' o statusie "
        "'Wysyłamy najczęściej w 1 dzień roboczy' bez ograniczenia min_qty > 1."
    )
    selected_product_data, product_page = result

    product_recap_data = product_page.content.recap.get_data()
    product_page_data = product_page.add_to_cart()
    product_page.overlays.promotions.click_buy_only_product()
    product_page.overlays.go_to_cart.click_go_to_cart()

    return SelectProductData(
        listing_data=selected_product_data,
        product_page_data=product_page_data,
        product=product_recap_data,
    )


def _prepare_client_session(
    page,
    context,
    runtime_env,
    auth_case: AuthSessionCase,
    *,
    use_production_email: bool,
    reusable_smoke_user_cache: dict[str, object],
):
    if not auth_case.authenticated and not auth_case.register_before_flow:
        return None

    cache_key = settings_cli.production_test_email if use_production_email else "default"
    cached_user = reusable_smoke_user_cache.get(cache_key)
    if cached_user is not None:
        user_data = cached_user
        if auth_case.authenticated:
            _login_with_cached_user(page, runtime_env, user_data)
        elif auth_case.register_before_flow:
            _logout_if_logged_in(page, runtime_env)
        return user_data

    user_data = ClientDataBuilder().with_required_terms().build()
    if use_production_email:
        user_data.email = settings_cli.production_test_email
    client_wrappers = ClientWrappers(page, context, runtime_env)
    assert client_wrappers.register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    if auth_case.register_before_flow and not auth_case.authenticated:
        client_wrappers.logout_client()
    reusable_smoke_user_cache[cache_key] = user_data
    return user_data


def _logout_if_logged_in(page, runtime_env) -> None:
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH).wait_loaded()
    if home.header.actions.is_my_account_available():
        home.open_account_page().logout_to_home_page()


def _login_with_cached_user(page, runtime_env, user_data) -> None:
    """Loguje użytkownika z cache w aktualnym BrowserContext (scope=function)."""
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH).wait_loaded()
    if not home.header.actions.is_my_account_available():
        home.open_login_overlay().log_client(user_data.email, user_data.password)


def _prepare_checkout_case(
    delivery_case: CheckoutDeliveryCase,
    *,
    comment: str,
    forced_email: str | None,
) -> CheckoutDeliveryCase:
    payment_objects = delivery_case.payment_objects
    purchaser_objects = delivery_case.purchaser_objects
    delivery_objects = delivery_case.delivery_objects

    if payment_objects is not None:
        payment_objects = replace(payment_objects, comment=comment)
    if forced_email and purchaser_objects is not None and hasattr(purchaser_objects, "email"):
        purchaser_objects = replace(purchaser_objects, email=forced_email)
    if forced_email and delivery_objects is not None and hasattr(delivery_objects, "email"):
        delivery_objects = replace(delivery_objects, email=forced_email)

    return replace(
        delivery_case,
        payment_objects=payment_objects,
        purchaser_objects=purchaser_objects,
        delivery_objects=delivery_objects,
    )


def _use_production_email_for_case(
    auth_case: AuthSessionCase,
    delivery_case: CheckoutDeliveryCase,
    runtime_env,
) -> bool:
    is_prod = runtime_env.server_name == "prod"
    return is_prod and auth_case.case_id == "logged_in" and delivery_case.case_id == "courier_service"


def _append_production_order_log(
    run_artifacts: RunArtifacts,
    sales_channel: str,
    order_number: str,
    total_to_pay: str,
) -> None:
    target = Path(run_artifacts.logs) / "production_orders.log"
    channel_header = f"[{sales_channel}]"
    placed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"placed_at={placed_at} | order_number={order_number} | total_to_pay={total_to_pay}\n"

    if not target.exists():
        target.write_text(f"{channel_header}\n{line}", encoding="utf-8")
        return

    content = target.read_text(encoding="utf-8")
    if channel_header not in content:
        with target.open("a", encoding="utf-8") as handle:
            if content and not content.endswith("\n"):
                handle.write("\n")
            handle.write(f"{channel_header}\n{line}")
        return

    with target.open("a", encoding="utf-8") as handle:
        handle.write(line)
