---
date: 2026-05-12T00:00:00+02:00
git_commit: ee7e62b2ad3517ed49a183807d9a91d284a259de
branch: feature/NN-24016-ai-w-pisaniu-testow-e2e
repository: qa-test-netquarner
topic: "Analiza migracji testów orders: Selenium (nc-functional-tests-py) → Playwright (qa-test-netquarner)"
tags: [research, migration, selenium, playwright, orders, e2e, gap-analysis]
last_updated: 2026-05-12
---

## Streszczenie

Przeprowadzono pełną analizę 15 testów E2E z suity `OrdersTestsNUXT` w repozytorium
`nc-functional-tests-py` pod kątem migracji do `qa-test-netquarner`.

Środowisko testowe: `https://komputronik-galak.test.netcorner.pl/`

Kluczowy wniosek: **4 testy można migrować natychmiast**, pozostałe 11 wymaga budowy
infrastruktury której jeszcze nie ma — głównie page objects panelu admina (bloker dla 10 testów)
oraz integracji z Mailhog (bloker dla 3 testów).

---

## Repozytorium źródłowe: nc-functional-tests-py

### Architektura Selenium

| Warstwa | Opis |
|---|---|
| Testy | `unittest` + `ddt` + `@data(DictDP(...))` |
| Orchestrator | `FunctionalObjects` — centralny obiekt przepływu |
| Page objects | Klasy z lokoratorami XPath jako class-level constants |
| Dane testowe | Słowniki Python w `TestData/pl_komputronik_nuxt/data_*.py` |
| Setup/teardown | Dziedziczenie z `KomputronikTestSetupNuxt` (screenshoty, driver quit) |
| Admin | `AdminPageObjects` — weryfikacja zamówień, zmiana statusów, tworzenie ofert |
| Email | `MailhogObject` — weryfikacja maili wysłanych przez sklep |

### Wzorzec testu (Selenium)

```python
@ddt
class TestOrderPrices(KomputronikTestSetupNuxt):
    @print_scenario_on_fail
    @data(DictDP(order_prices, "order_price"))
    def test_order_prices(self, test_data):
        Page.FunctionalObjects(self.driver).select_test_product(self.base_url, test_data["category"])
        Page.FunctionalObjects(self.driver).process_order_full_checkout(test_data)
        test_data["typ_data"] = Page.CheckoutThankYouPage(self.driver).get_typ_order_data()
        Page.AdminPageObjects(self.driver).assert_admin_order_details(self.admin_url, test_data)
```

---

## Analiza każdego testu Selenium

### 1. TestOrderBigSizeWithLift

- **Co testuje:** Zamówienie produktu gabarytowego z usługą wniesienia do lokalu.
- **Przepływ:** Dodaje produkt gabarytowy (`DimensionProductKey.G1`) → pełny checkout → weryfikacja w adminie.
- **Dane:** `order_big_size` — `order_as: NON_REGISTERED`, dostawca `KURJER_BIG_SIZE_WITH_LIFT`.
- **Weryfikacja:** `AdminPageObjects.assert_admin_order_details()` — porównuje dane z TYP z danymi w panelu admina.
- **Blokery migracji:** Brak `DeliveryTypes.BIG_SIZE_WITH_LIFT` w enum; brak admin page objects.

### 2. TestOrderBigSizeWithoutLift

- **Co testuje:** Zamówienie produktu gabarytowego BEZ wniesienia.
- **Przepływ:** Identyczny jak powyższy, inny typ dostawy (`BIG_SIZE_WITHOUT_LIFT`).
- **Dane:** `order_big_size_without_lift`.
- **Blokery migracji:** Jak wyżej — nowy typ dostawy + admin.

### 3. TestOrderCancel

- **Co testuje:** Anulowanie zamówienia przez klienta z poziomu "Moje Konto".
- **Przepływ:** Rejestracja → wybór produktu → checkout → wejście na stronę zamówienia → kliknięcie "Anuluj" → asercja statusu lub toast.
- **Asercje:** Albo pojawia się toast negatywny (brak możliwości anulowania) albo status = `Anulowane`.
- **Dane:** `order_cancel`.
- **Blokery migracji:** Brak `OrderDetailPage` w MyAccount (strona szczegółów zamówienia klienta); brak obsługi przycisku "Anuluj" i odczytu statusu.

### 4. TestOrderCartOffer

- **Co testuje:** Ofertę koszykową — tworzenie w adminie, wysyłka mailem, weryfikacja wartości.
- **Przepływ:** Rejestracja → admin tworzy ofertę → email z URL → klient otwiera URL oferty → cena oferty porównana z koszykiem → checkout → weryfikacja deaktywacji oferty.
- **Asercje:** URL z admina == URL z emaila; wartość oferty == suma koszyka; wartość oferty == admin summary minus shipping; oferta dezaktywowana po zamówieniu.
- **Blokery migracji:** Admin page objects (tworzenie oferty, wysyłka maila) + Mailhog + `CartOfferObjects` (strona oferty koszykowej).

### 5. TestOrderCompanyData

- **Co testuje:** Zamówienie z danymi firmowymi — weryfikacja NIP w panelu admina.
- **Przepływ:** Rejestracja (opcjonalna) → wybór produktu → checkout z nabywcą firmowym → TYP → admin.
- **Asercje:** NIP z danych testowych pojawia się w danych nabywcy w panelu admina.
- **Dane:** Dwa warianty: `registered` i `non_registered`.
- **Blokery migracji:** Admin page objects (odczyt danych nabywcy). Sama część checkout działa już przez `company_checkout_purchaser()`.
- **Uwaga:** Checkout z firmowym nabywcą jest już obsługiwany przez `CheckoutPurchaserDataBuilder().build_company()`.

### 6. TestOrderDigitalLicense

- **Co testuje:** Zamówienie licencji cyfrowych — 16 wariantów (pojedyncze/wiele, z/bez produktu fizycznego, prywatny/firma, zarejestrowany/niezarejestrowany).
- **Przepływ:** Rejestracja → wybór produktu cyfrowego z kategorii + filtrów → opcjonalnie wielokrotne licencje + produkt fizyczny → checkout → admin.
- **Asercje:** Delegowane do `AdminPageObjects.assert_admin_order_details()`.
- **Blokery migracji:** Brak obsługi produktów cyfrowych w `SelectProductWrappers` (flaga `digital=True` wchodząca w specjalny flow wyboru produktu); admin page objects.

### 7. TestOrderDimensionModule

- **Co testuje:** Moduł wymiarów — 28 kombinacji produktów gabarytowych, weryfikacja alertów koszyka i możliwości złożenia zamówienia.
- **Przepływ:** Dodaje 1 lub 2 produkty po ID → asercja przycisku "kontynuuj" aktywna → checkout → admin.
- **Asercje:** `assert_continue_to_order_button_and_alert(active=True)` + admin verification.
- **Blokery migracji:** Brak logiki cart restriction (sprawdzanie alertów ograniczeń koszyka); admin page objects.

### 8. TestOrderMatrixVsList

- **Co testuje:** Zamówienie z widoku matrycy vs listy produktów — walidacja tras zakupowych dla różnych kodów pocztowych.
- **Przepływ:** Admin konfiguracja (wymuszenie kodu pocztowego dla ścieżki list) → wybór produktu → checkout.
- **Dane:** `order_matrix` i `order_list` — różne kody pocztowe odbiorcy.
- **Blokery migracji:** Admin konfiguracja (zmiana ustawień pocztowych przed testem); choć checkout sam w sobie jest już obsługiwany.

### 9. TestOrderOzo

- **Co testuje:** Mechanizm OZO (Okazja Za Okazję) — sprzedaż limitowana, licznik sprzedanych/pozostałych sztuk.
- **Przepływ (setUp/tearDown):** Reset liczników OZO w adminie przed i po każdym teście.
- **test_product_ozo_limited_sale:** Loguje użytkownika → pobiera dane OZO z homepage → składa zamówienie → weryfikuje liczniki na homepage i stronie produktu.
- **test_ozo_limited_sale_logged/guest:** Próba zakupu po wyczerpaniu limitu → asercja alertu `LIMITED_SALE_EXCEEDED`.
- **Blokery migracji:** Admin (reset OZO); OZO box component na stronie głównej; detekcja `limited_sale_status` na karcie produktu.

### 10. TestOrderPartnerStorehouse

- **Co testuje:** Zamówienie z dostawą do salonu partnerskiego — weryfikacja emaili do partnera.
- **Przepływ:** Wybór produktu → checkout z dostawą do salonu → TYP → Mailhog (sprawdza liczbę maili dla zamówienia).
- **Asercje:** Liczba emaili: 2 (non-test env) lub 3 (test env).
- **Blokery migracji:** Mailhog integration; admin page objects (opcjonalnie).
- **Uwaga:** Typ dostawy `STORE_PICKUP` już istnieje w `DeliveryTypes`.

### 11. TestOrderPrices

- **Co testuje:** Weryfikację cen zamówienia — porównanie TYP z danymi w adminie.
- **Przepływ:** Wybór produktu z kategorii → checkout → TYP → admin.
- **Asercje:** Delegowane do `AdminPageObjects.assert_admin_order_details()`.
- **Dane:** `order_prices` — konkretna kategoria produktu testowego.
- **Blokery migracji:** Admin page objects (weryfikacja cen).
- **Uwaga:** Sam checkout jest w pełni obsługiwany.

### 12. TestOrderStatuses

- **Co testuje:** Cykl statusów zamówienia — zmiana statusów w adminie, weryfikacja na koncie klienta i emailach.
- **Przepływ:** Wybór produktu → checkout → TYP → admin zmienia statusy iteracyjnie → asercja statusu w "Moje Konto" → Mailhog weryfikuje emaile o statusach.
- **Asercje:** Status na koncie klienta odpowiada statusowi zmienionemu w adminie; każdy status pojawia się w emailu.
- **Blokery migracji:** Admin (zmiana statusów zamówienia); `OrderDetailPage` z odczytem statusu; Mailhog.

### 13. TestOrderWithDhlPop

- **Co testuje:** Zamówienie z dostawą do punktu DHL POP.
- **Przepływ:** Opcjonalna rejestracja → wybór produktu → checkout z DHL POP → TYP → admin.
- **Asercje:** Delegowane do `AdminPageObjects.assert_admin_order_details()`.
- **Dane:** `dhlpop_non_registered` i `dhlpop_registered`.
- **Blokery migracji:** Admin page objects. Sam checkout jest obsługiwany (`DeliveryTypes.DHL_POP`).
- **Uwaga:** Test ten jest de facto pokryty przez `test_basic_orders.py` (case `dhl_pop`).

### 14. TestOrderWithInpost

- **Co testuje:** Zamówienie z dostawą do paczkomatu Inpost.
- **Przepływ:** Wybór produktu → checkout z Inpost → TYP → admin.
- **Asercje:** Delegowane do `AdminPageObjects.assert_admin_order_details()`.
- **Dane:** `inpost_non_registered`.
- **Blokery migracji:** Admin page objects. Sam checkout jest obsługiwany (`DeliveryTypes.INPOST`).
- **Uwaga:** Test ten jest de facto pokryty przez `test_basic_orders.py` (case `inpost`).

### 15. TestOrderWithMinQtyProduct

- **Co testuje:** Zamówienie produktu z minimalną ilością w zamówieniu — weryfikacja, że koszyk respektuje `min_qty`.
- **Przepływ:** Dodaje produkt po ID z callable `product_page_function` pobierającym `min_qty` → odczyt koszyka → checkout → TYP → admin.
- **Asercje:** Ilość w koszyku == `min_qty` z karty produktu; cena w TYP == cena w adminie.
- **Blokery migracji:** Detekcja `min_qty` z komponentu karty produktu (brak w `product_components.py`); admin page objects.

---

## Repozytorium docelowe: qa-test-netquarner

### Architektura Playwright

| Warstwa | Opis | Lokalizacja |
|---|---|---|
| Testy | `pytest` + `pytest.mark.parametrize` + `@pytest.mark.scenario` | `qa/e2e/netcorner/nuxt/pl/tests/` |
| Wrappers/Flows | Klasy opakowujące wieloetapowe przepływy biznesowe | `lib/flows/` |
| Page objects | `BasePage` / `BaseComponent` z ROOT_SELECTOR, lokatory w konstruktorze | `lib/page_objects/` |
| Dane testowe | Dataclassy + builderzy + generatory przypadków z `case_id` | `lib/test_data/` |
| Fixtures | `conftest.py` hierarchia: root → qa → e2e → nuxt/pl | wielopoziomowe |
| Step tracing | `step_context()` z `qa.e2e.netcorner.lib.step_api` (nie `allure.step`) | `qa/e2e/netcorner/lib/step_api.py` |

### Co już ISTNIEJE (nie duplikować)

| Komponent | Lokalizacja | Pokrywa |
|---|---|---|
| `SelectProductWrappers` | `lib/flows/select_product_wrappers.py` | Wybór produktu z listingu → koszyk |
| `CartAndCheckoutWrappers` | `lib/flows/cart_and_checkout_wrappers.py` | Koszyk → checkout → TYP |
| `ClientWrappers` | `lib/flows/client_wrappers.py` | Rejestracja i wylogowanie |
| `DeliveryTypes.INPOST/DHL_POP/COURIER_SERVICE/STORE_PICKUP` | `checkout_data_models.py` | Wszystkie 4 podstawowe typy dostawy |
| `checkout_delivery_cases()` | `checkouts_generators.py` | 8 przypadków (4 typy × prywatny/firma) |
| `auth_session_cases()` | `client_generators.py` | logged_in + anonymous |
| `CheckoutPurchaserDataBuilder().build_company()` | `checkouts_generators.py` | Nabywca firmowy z NIP |
| `MyAccountPage` + `MyAccountComponent` | `pages/my_account_page.py` | Moje Konto (menu, wylogowanie) |
| Overlays: Inpost, DHL Pop, Kurier, Salon | `overlays/checkout/` | Modalne wyboru dostawy |
| `CartPage`, `CheckoutPage`, `ProductPage` | `pages/` | Strony sklepu |

### Czego NIE MA (luki infrastrukturalne)

| Brakujący element | Bloker dla testów | Priorytet |
|---|---|---|
| **Admin panel page objects** | 10/15 testów (wszystkie z `assert_admin_order_details`) | KRYTYCZNY |
| **Mailhog integration** | TestOrderStatuses, TestOrderPartnerStorehouse, TestOrderCartOffer | WYSOKI |
| **OrderDetailPage** (konto klienta — szczegóły zamówienia) | TestOrderCancel, TestOrderStatuses | WYSOKI |
| **Anulowanie zamówienia** (przycisk + weryfikacja statusu) | TestOrderCancel | WYSOKI |
| `DeliveryTypes.BIG_SIZE_WITH_LIFT` / `BIG_SIZE_WITHOUT_LIFT` | TestOrderBigSizeWithLift/Without | ŚREDNI |
| Overlay big size delivery | TestOrderBigSizeWithLift/Without | ŚREDNI |
| Obsługa produktów cyfrowych w `SelectProductWrappers` | TestOrderDigitalLicense | ŚREDNI |
| Detekcja `min_qty` z `ProductComponents` | TestOrderWithMinQtyProduct | NISKI |
| Cart restriction assertions | TestOrderDimensionModule | NISKI |
| OZO box component (homepage) | TestOrderOzo | NISKI |
| Limited sale status na karcie produktu | TestOrderOzo | NISKI |
| Cart offer page objects | TestOrderCartOffer | NISKI |

---

## Klasyfikacja testów wg gotowości

### Tier 1 — Gotowe natychmiast (infrastruktura istnieje)

| Test Selenium | Odpowiednik Playwright | Uwagi |
|---|---|---|
| `TestOrderWithInpost` | Pokryty przez `test_basic_orders.py[inpost]` | Można wydzielić jako dedykowany test |
| `TestOrderWithDhlPop` | Pokryty przez `test_basic_orders.py[dhl_pop]` | Można wydzielić jako dedykowany test |
| `TestOrderPrices` | Nowy `test_orders_prices.py` | Bez weryfikacji admina — tylko numer zamówienia |
| `TestOrderCompanyData` | Nowy `test_orders_company_data.py` | Pokryty przez `courier_service_company` case; bez admina |

### Tier 2 — Potrzeba umiarkowanej nowej infrastruktury (bez admina)

| Test Selenium | Co zbudować |
|---|---|
| `TestOrderCancel` | `OrderDetailPage` + przycisk anulowania + odczyt statusu |
| `TestOrderWithMinQtyProduct` | Detekcja `min_qty` w `ProductComponents` + nowe przypadki testowe |
| `TestOrderMatrixVsList` | Opcjonalnie: skrócona wersja bez admin setup (lub z fixture admin config) |

### Tier 3 — Wymaga admin panel page objects (duży scope)

| Test Selenium | Dodatkowe zależności poza adminiem |
|---|---|
| `TestOrderBigSizeWithLift/Without` | Nowy `DeliveryTypes` + overlay |
| `TestOrderStatuses` | Admin (zmiana statusów) + Mailhog + OrderDetailPage |
| `TestOrderDigitalLicense` | Obsługa produktów cyfrowych w selectów |
| `TestOrderDimensionModule` | Cart restriction logic |
| `TestOrderPartnerStorehouse` | Mailhog |
| `TestOrderCartOffer` | Admin (tworzenie oferty) + Mailhog + cart offer page |
| `TestOrderOzo` | Admin (reset OZO) + OZO components |

---

## Istniejący test bazowy jako wzorzec

`qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py` — pełen wzorzec:

```
1. Opcjonalna rejestracja (_prepare_client_session)
2. SelectProductWrappers.select_test_product(listings_data)
3. Asercje: listing ↔ product page (status, cena)
4. dump_data(...)
5. CartAndCheckoutWrappers.process_cart()
6. CartAndCheckoutWrappers.process_checkout(delivery, purchaser, payment)
7. Asercja: order_number nie jest pusty
```

Efektywne pokrycie: 2 auth_case × 8 delivery_case = **16 kombinacji** ze stackowanego `@pytest.mark.parametrize`.

---

## Kluczowe różnice architektoniczne

| Aspekt | Selenium | Playwright |
|---|---|---|
| Framework testowy | `unittest` + `ddt` | `pytest` + `parametrize` |
| Dane testowe | Słowniki | Dataclassy (frozen gdzie możliwe) |
| Lokatory | Osobne pliki `*Locators.py` z XPath | W konstruktorze komponentu; `data-*` > semantic |
| Wzorzec przepływu | `FunctionalObjects` jako god-object | Dedykowane wrappers per przepływ |
| Setup/teardown | Klasy bazowe `setUp/tearDown` | pytest fixtures + conftest hierarchy |
| Admin weryfikacja | Wbudowana w każdy test | Nie istnieje — BLOKER |
| Mailhog | Wbudowany `MailhogObject` | Nie istnieje — BLOKER |
| Logowanie kroków | `@print_scenario_on_fail` | `step_context()` + allure |

---

## Odwołania do kodu

- Selenium orchestrator: `nc-functional-tests-py/TestCases/.../Lib/PageObjects/FunctionalObjects.py:139` — `process_order_full_checkout`
- Playwright checkout wrapper: `qa/e2e/netcorner/nuxt/pl/lib/flows/cart_and_checkout_wrappers.py:132` — `process_checkout`
- Istniejące delivery types: `qa/e2e/netcorner/nuxt/pl/lib/test_data/checkout/checkout_data_models.py:10`
- Wzorzec testu: `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py:23`
- MyAccount page: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/pages/my_account_page.py:15`
- Kontrakt page objects: `docs/E2E_PAGE_OBJECT_CONTRACT.md`

---

## Appendix — status wdrożenia (2026-05-13)

- Faza 2 została domknięta implementacyjnie: 16/16 testów dostarczonych, z czego 6 oznaczono jako alpha/smoke-warunkowe.
- Dostarczone testy produktowe (nowe):
  - `tests_products/test_add_product_to_cart.py`
  - `tests_products/test_product_availability.py`
  - `tests_products/test_temporarily_unavailable_products.py`
  - `tests_products/test_omnibus_prices.py`
  - `tests_products/test_product_labels.py`
  - `tests_products/test_product_comparison.py`
  - `tests_products/test_add_product_opinion.py`
  - `tests_products/test_products_list_filtering.py`
  - `tests_products/test_product_ozo.py`
  - `tests_products/test_products_list_sezam_filter.py` (alpha/beta hardening)
  - `tests_products/test_adhoc_product.py` (alpha/beta hardening)
- Dostarczone testy forms/account (alpha):
  - `tests_forms/test_forms_checkout.py` (wariant checkout: kurier + BLIK)
  - `tests_forms/test_forms_account.py`
  - `tests_account/test_crud_purchaser_receiver_account.py`
  - `tests_account/test_crud_purchaser_receiver_checkout.py` (wariant checkout: kurier + BLIK)
- Dodane/rozszerzone komponenty PO:
  - `comparison_component.py`
  - `omnibus_price_component.py`
  - `product_opinion_component.py`
  - rozszerzenie `hero_component.py` o OZO widget checks.
- Wydzielono Faza 2-beta dla hardeningu danych produktowych (Sezam i Adhoc), aby usunąć warunkowe `skip` po wskazaniu stabilnych danych.
