---
date: 2026-05-12T00:00:00+02:00
git_commit: ee7e62b2ad3517ed49a183807d9a91d284a259de
branch: feature/NN-24016-ai-w-pisaniu-testow-e2e
repository: qa-test-netquarner
topic: "Plan implementacji migracji OrdersTestsNUXT: Selenium → Playwright"
tags: [plan, migration, orders, e2e, playwright, sprints, mailhog]
last_updated: 2026-05-14
---

# Plan migracji OrdersTestsNUXT

## Checkpoint (2026-05-13)

- Równolegle do planu Orders uruchomiono Fazę 2 (Products) z `migration_todo.md`.
- Dostarczono 8 testów produktowych (Wave 1 + część Wave 2), które budują brakującą bazę PO pod dalszą migrację.
- Dostarczono `test_product_ozo.py` oraz rozpoczęto Faza 2-alfa dla forms/CRUD (wariant checkout: kurier + BLIK).
- Wydzielono Faza 2-beta dla hardeningu danych produktowych:
  - `test_products_list_sezam_filter.py` — stabilny Sezam bez `skip`
  - `test_adhoc_product.py` — stabilny ad-hoc bez `skip`
- Następny krok po wznowieniu: domknięcie Fazy 2-beta i przejście do Fazy 3 (Orders bez admina).

## Checkpoint (2026-05-14)

- Faza 3 została domknięta:
  - `test_orders_cancel.py`
  - `test_orders_min_qty.py`
  - `test_monitoring_checkout.py`
- Krytyczny blocker admina (`DEBT-001`) został zdjęty.
- Dostarczono współdzielony moduł `qa/e2e/netcorner/admin/` z:
  - loginem do admina
  - wyborem kontekstu sprzedaży
  - listą zamówień
  - szczegółami zamówienia
  - zmianą statusu zamówienia
  - wrapperem `AdminWrappers`
  - fixture `admin_panel`
- Faza 4 została odblokowana infrastrukturalnie i weszła w realizację.
- Pierwszy test Fazy 4 jest domknięty: `test_orders_company_data.py` (2 warianty PASSED).
- Faza 4-alfa została domknięta:
  - `test_orders_company_data.py`
  - `test_orders_prices.py`
- Faza 4-beta i 4-gamma zostały wdrożone:
  - `test_orders_matrix_vs_list.py`
  - `test_orders_big_size_with_lift.py`
  - `test_orders_big_size_without_lift.py`
  - `test_orders_dimension_module.py`
  - `test_split_payment.py`
  - `test_aggregator.py`
  - `test_aggregator_promo_code.py`
- Weryfikacja live zakresu beta+gamma: `8 passed, 3 skipped`.
- Skipy środowiskowe:
  - `test_orders_matrix_vs_list.py` — drift checkoutu / kodów pocztowych na env
  - `test_aggregator_promo_code.py` — produkt z agregatora nie dochodzi stabilnie do koszyka na env
- Główny blocker przesunął się z admin page objects na backlog implementacyjny Fazy 4 oraz brakujące rozszerzenia Mailhog potrzebne dla Fazy 5.

## Next Up

1. Wejść w Fazę 4-delta: pierwsza fala `CartRestrictionTestsNUXT` na gotowym admin API.
2. Ustabilizować środowiskowe skipy z Fazy 4-beta/gamma:
   - `test_orders_matrix_vs_list.py`
   - `test_aggregator_promo_code.py`
3. Rozszerzyć Mailhog (`count_mails_matching`, `has_mail_with_subject_containing`, nowe subjecty) i wejść w Fazę 5.

## Cel

Przepisanie 15 testów z
`nc-functional-tests-py/TestCases/NetCornerProducts/pl_komputronik_nuxt/Test/OrdersTestsNUXT/`
do
`qa-test-netquarner/qa/e2e/netcorner/nuxt/pl/tests/tests_orders/`
z zachowaniem architektury i wytycznych repozytorium Playwright.

Środowisko testowe: `https://komputronik-galak.test.netcorner.pl/`

---

## Stan wyjściowy

Istniejący test bazowy `test_basic_orders.py` pokrywa już:
- 4 typy dostawy × 2 typy klienta = 16 kombinacji
- Inpost i DHL Pop są de facto przetestowane

Pierwotnie brakująca infrastruktura zidentyfikowana w `research.md`:
- Admin panel page objects (bloker krytyczny dla 10/15 testów) — DONE
- Mailhog integration (bloker dla 3 testów) — nadal otwarte rozszerzenia Sprint 4
- OrderDetailPage — strona szczegółów zamówienia (dla cancel, statuses) — baza dla cancel DONE

---

## Sprint 1 — Testy gotowe natychmiast

**Scope:** Testy, dla których cała infrastruktura już istnieje.
**Nakład:** ~1–2 dni

### 1.1 test_orders_company_data.py

**Źródło:** `TestOrderCompanyData.py`
**Co robi:** Zamówienie z nabywcą firmowym (NIP), 2 warianty: zarejestrowany / niezarejestrowany.
**Dostępna infrastruktura:** `company_checkout_purchaser()`, `auth_session_cases()`, `CartAndCheckoutWrappers`.
**Pominięte (bez admina):** Weryfikacja NIP w panelu admina → TODO komentarz.

```python
# Nowy plik: tests_orders/test_orders_company_data.py
pytestmark = [pytest.mark.e2e, pytest.mark.orders]

@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda c: c.case_id)
@pytest.mark.scenario("Zamówienie z danymi firmowymi")
def test_orders_company_data(page, context, runtime_env, auth_case):
    # company_checkout_purchaser() z tax_identification_number="7770020640"
    # TODO: weryfikacja NIP w adminie po zbudowaniu admin page objects
```

### 1.2 test_orders_prices.py

**Źródło:** `TestOrderPrices.py`
**Co robi:** Zamówienie z weryfikacją cen.
**Dostępna infrastruktura:** Pełny checkout.
**Pominięte (bez admina):** Porównanie cen TYP vs admin → TODO komentarz.

### 1.3 Wydzielone testy dedykowane dla Inpost i DHL Pop

**Źródła:** `TestOrderWithInpost.py`, `TestOrderWithDhlPop.py`
**Uwaga:** Funkcjonalność pokryta przez `test_basic_orders.py`. Testy te można wydzielić
jako `test_orders_pickup_points.py` z dedykowanymi scenariuszami opisowymi, jeśli
wymagany jest oddzielny marker/raportowanie.

---

## Sprint 2 — OrderDetailPage i anulowanie

**Scope:** Budowa `OrderDetailPage` + test anulowania zamówienia.
**Nakład:** ~2–3 dni

### 2.1 Nowe page objects: OrderDetailPage

**Lokalizacja:** `lib/page_objects/pages/order_detail_page.py`
**Co obsługuje:**
- Odczyt numeru zamówienia
- Odczyt statusu zamówienia
- Przycisk "Anuluj zamówienie"
- Obsługa toastu negatywnego (brak możliwości anulowania)

**Lokatory do zbadania** na `https://komputronik-galak.test.netcorner.pl/customer/account/orders`:
- Szczegóły zamówienia: `data-*` atrybuty na elementach statusu
- Przycisk anulowania: szukać `get_by_role("button", name="Anuluj")`
- Toast: wykorzystać istniejący `toast_overlay.py`

### 2.2 Rozszerzenie MyAccountComponent

**Lokalizacja:** `lib/page_objects/components/my_account_component.py`
**Co dodać:** Metoda nawigacji do konkretnego zamówienia po numerze.

### 2.3 test_orders_cancel.py

**Źródło:** `TestOrderCancel.py`
**Flow:**
1. Rejestracja + checkout (zarejestrowany klient)
2. Nawigacja do zamówienia w MyAccount
3. Próba anulowania
4. Asercja: toast negatywny (nie można anulować) LUB status = "Anulowane"

### 2.4 test_orders_min_qty.py

**Źródło:** `TestOrderWithMinQtyProduct.py`
**Co dodać do infrastruktury:**
- Detekcja `min_qty` w `ProductComponents` (`get_min_qty_for_order()`)
- Odczyt ilości produktu w `CartComponents`
**Asercja:** `qty_in_cart == min_qty_from_product_page`

---

## Sprint 3 — Admin panel page objects (DONE)

**Scope:** Budowa page objects panelu admina — odblokowuje Fazę 4 i część Fazy 5.
**Nakład:** ~5–8 dni
**Lokalizacja proponowana:** `qa/e2e/netcorner/nuxt/pl/lib/page_objects/pages/admin/`

**Status:** DONE (2026-05-14)

### 3.1 Zakres admin page objects (minimalny do odblokowania testów)

| Funkcja admina | Potrzebna dla |
|---|---|
| Login do admina | Wszystkie testy z adminem |
| Widok zamówień — wyszukanie po numerze | Wszystkie weryfikacje zamówień |
| Odczyt danych zamówienia (nabywca, cena, status) | TestOrderCompanyData, TestOrderPrices, TestOrderBigSize*, TestOrderWithInpost, TestOrderWithDhlPop |
| Zmiana statusu zamówienia | TestOrderStatuses |
| Tworzenie oferty koszykowej + wysyłka | TestOrderCartOffer |
| Reset liczników OZO | TestOrderOzo |
| Konfiguracja kodów pocztowych | TestOrderMatrixVsList |

### 3.2 Proponowana architektura admin page objects

```
lib/page_objects/pages/admin/
├── admin_login_page.py
├── admin_orders_page.py          # lista zamówień
├── admin_order_detail_page.py    # szczegóły zamówienia (odczyt + akcje)
└── admin_configuration_page.py  # konfiguracja sklepu
```

### 3.3 Wrapper admina

```
lib/flows/admin_wrappers.py       # AdminWrappers — login, nawigacja, weryfikacja zamówień
```

### 3.4 Testy odblokowane po Sprint 3

Po zbudowaniu admin page objects można domknąć TODO w:
- `test_orders_company_data.py` — weryfikacja NIP
- `test_orders_prices.py` — porównanie cen
- Nowe: `test_orders_big_size.py`, `test_orders_statuses.py` (częściowo)

Status po wdrożeniu:
- `test_orders_company_data.py` — DONE
- `test_orders_prices.py` — DONE
- Faza 4 wymaga już głównie implementacji scenariuszy, nie budowy fundamentu admina

---

## Sprint 4 — Mailhog: uzupełnienie istniejącej infrastruktury

**Scope:** `MailInboxService` już istnieje (`qa/e2e/netcorner/mailhog/`) i jest używany w
`test_password_modifications.py`. Sprint 4 dokłada brakujące możliwości potrzebne testom orders.
**Nakład:** ~1–2 dni (infrastruktura częściowo gotowa)

### 4.0 Stan istniejący `MailInboxService`

**Plik:** `qa/e2e/netcorner/mailhog/lib/flows/inbox_flow.py`
**Fixture:** `mail_inbox` w `qa/e2e/netcorner/conftest.py`

Dostępne metody:

| Metoda | Opis |
|---|---|
| `get_link_from_subject(context, recipient, subject, link_regex)` | Otwiera nową kartę, szuka maila po wzorcu tematu i adresie, zwraca link |
| `get_password_reset_link(context, recipient)` | Specjalizacja dla resetu hasła |
| `get_order_mail_link(context, recipient, shop_host, order_number)` | Specjalizacja dla potwierdzenia zamówienia |

Dostępne `MailSubjects`:

| Stała | Wzorzec tematu |
|---|---|
| `PASSWORD_RESET` | `Odzyskanie hasła - Komputronik.pl` |
| `LOGIN` | `Logowanie` |
| `NEW_USER_REGISTERED` | `Zarejestrował się nowy użytkownik` |
| `ORDER_PROBLEM` | `Komputronik.pl - Problem z zamówieniem` |
| `order_shop_number(shop_host, order_number)` | `Zamówienie sklepu {host} numer: {nr}` — dla maili do partnera |
| `order_summary_komputronik(order_number)` | `Zamówienie {nr} - Komputronik.pl` — dla klienta |

### 4.1 Czego brakuje (potrzeby testów orders)

**Plik do rozszerzenia:** `qa/e2e/netcorner/mailhog/lib/flows/inbox_flow.py`

| Brakująca metoda | Potrzebna dla |
|---|---|
| `count_mails_matching(context, recipient, subject, timeout_ms)` | `TestOrderPartnerStorehouse` — asercja `len(emails) == 2 lub 3` |
| `has_mail_with_subject_containing(context, recipient, text)` | `TestOrderStatuses` — sprawdza czy mail z nazwą statusu istnieje |
| `get_cart_offer_link(context, recipient)` | `TestOrderCartOffer` — URL oferty z maila |

**Plik do rozszerzenia:** `qa/e2e/netcorner/mailhog/lib/mail_subjects.py`

| Brakująca stała | Potrzebna dla |
|---|---|
| `ORDER_STATUS_CHANGED` (z dynamiczną nazwą statusu) | `TestOrderStatuses` |
| `CART_OFFER` | `TestOrderCartOffer` |
| `PARTNER_STOREHOUSE_ORDER` | `TestOrderPartnerStorehouse` (partner notification) |

**Uwaga architektoniczna:** Metoda `count_mails_matching` musi iterować wiadomości bez
otwierania każdej z nich — wymaga rozszerzenia `InboxPage.count_messages_by_filter()`.

### 4.2 Testy odblokowane po Sprint 4

| Test | Co weryfikuje przez Mailhog |
|---|---|
| `test_orders_statuses.py` | Email dla każdej zmiany statusu zawiera nazwę statusu w temacie |
| `test_orders_partner_storehouse.py` | Liczba maili do partnera: 2 (non-test) lub 3 (test env) |
| `test_orders_cart_offer.py` | URL oferty z emaila == URL z panelu admina |

---

## Sprint 5 — Testy specjalistyczne

**Scope:** Pozostałe testy wymagające specyficznej infrastruktury.
**Nakład:** ~4–6 dni

### 5.1 test_orders_digital_license.py

**Źródło:** `TestOrderDigitalLicense.py` (16 wariantów)
**Co dodać:** Filtr `digital=True` w `SelectProductWrappers` (wybór produktu z kategorii
licencji cyfrowych); obsługa multi-license (dodanie kilku produktów cyfrowych).

### 5.2 test_orders_dimension_module.py

**Źródło:** `TestOrderDimensionModule.py` (28 kombinacji)
**Co dodać:** `CartRestrictionComponent` — asercja alertów ograniczeń koszyka przy
produktach gabarytowych.

### 5.3 test_orders_cart_offer.py

**Źródło:** `TestOrderCartOffer.py`
**Wymaga:** Admin (Sprint 3) + Mailhog (Sprint 4) + `CartOfferPage`.

### 5.4 test_orders_ozo.py

**Źródło:** `TestOrderOzo.py`
**Wymaga:** Admin reset OZO (Sprint 3) + `OzoBoxComponent` na homepage +
`LimitedSaleComponent` na karcie produktu.

---

## Niezmienne wytyczne architektury (przy każdym sprincie)

1. **Markery:** `pytestmark = [pytest.mark.e2e, pytest.mark.orders]` + `@pytest.mark.scenario(...)`
2. **Parametryzacja:** `pytest.mark.parametrize` + `case_id` + dataclassy
3. **Step tracing:** `step_context()` z `qa.e2e.netcorner.lib.step_api`
4. **Page objects:** ROOT_SELECTOR + lokatory w `__init__` + intent API
5. **Asercje:** Tylko w teście, nie w page objects; opisowe komunikaty po polsku
6. **Dane:** Dataclassy (frozen) + builder pattern + generatory przypadków
7. **Zakaz:** Fallback chains, `time.sleep()`, lokatory globalne `page.locator()` w komponentach
8. **Admin TODO:** Jeśli brak admina — komentarz `# TODO: admin verification (Sprint 3)`

---

## Odwołania

- Szczegółowa analiza testów: `thoughts/selenium_migration/research.md`
- Gotowy prompt do AI: `thoughts/selenium_migration/migration_prompt.md`
- Ticket admin panel: `thoughts/selenium_migration/admin_panel_ticket.md`
- Kontrakt page objects: `docs/E2E_PAGE_OBJECT_CONTRACT.md`
- Wzorzec testu: `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py`
