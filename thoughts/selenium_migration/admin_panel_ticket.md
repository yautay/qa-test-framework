---
type: debt
priority: critical
created: 2026-05-12T00:00:00+02:00
status: done
resolved: 2026-05-14
tags: [admin, page-objects, playwright, e2e, migration, orders, blocker]
keywords: [admin panel, order verification, admin page objects, AdminWrappers, order detail admin, status change admin]
patterns: [admin login, order detail page, status change, promo code admin, cart offer admin, OZO reset]
---

# DEBT-001: Admin panel page objects dla suity e2e nuxt pl

## Opis

Brak page objects panelu admina w `qa-test-netquarner` blokuje migrację **10 z 15** testów
z suity `OrdersTestsNUXT` oraz większości testów z `PromotionsTestsNUXT`,
`CartRestrictionTestsNUXT`, `SplitPaymentTestsNUXT`, `EmployeeProgramTestsNUXT`
i `SmokeTestsNUXT`.

W repozytorium Selenium istnieje `AdminPageObjects` w
`TestCases/NetCornerProducts/admin_panel/Lib/PageObjects/` który obsługuje cały panel.
W Playwright repo nie ma odpowiednika.

## Kontekst

Środowisko testowe admina: `https://komputronik-galak.test.netcorner.pl/admin/`
Dane dostępowe: z `settings.py` w starym repo lub `settings_cli.py` w nowym.

Testy blokowane przez ten dług (z `migration_todo.md`):

| Faza | Testy |
|---|---|
| Faza 4 | TestOrderBigSizeWithLift, TestOrderBigSizeWithoutLift, TestOrderDimensionModule, TestOrderCompanyData (TODO domknięcie), TestOrderPrices (TODO domknięcie), TestSplitPayment, TestAggregator, TestAggregatorPromoCode |
| Faza 5 | TestOrderStatuses, TestOrderPartnerStorehouse, TestOrderCartOffer, TestOrderOzo, TestEmployeeProgram* (6), SmokeTestsNUXT/TestOrders |
| Faza 6 | TestPromotions* (4) |
| Faza 7 | CartRestrictionTestsNUXT (29 testów) |

## Implementation (2026-05-14)

Zaimplementowano jako `qa/e2e/netcorner/admin/` — nowy moduł analogiczny do `mailhog/`,
współdzielony między wszystkimi suitami netcorner (nie wewnątrz `nuxt/pl/`).

### Dostarczone pliki

```
qa/e2e/netcorner/admin/
├── __init__.py
└── lib/
    ├── __init__.py
    ├── config.py                          # resolve_admin_env(), AdminEnv, credentials
    ├── flows/
    │   ├── __init__.py
    │   └── admin_wrappers.py              # AdminWrappers — open_admin, get_order_data, assert_order_details, change_order_status
    ├── page_objects/
    │   ├── __init__.py
    │   └── pages/
    │       ├── __init__.py
    │       ├── admin_login_page.py        # login form (confirmed live)
    │       ├── admin_context_page.py      # sales channel selector (confirmed live)
    │       ├── admin_orders_page.py       # orders list + open_order()
    │       └── admin_order_detail_page.py # get_all_data(), change_status()
    └── test_data/
        ├── __init__.py
        └── admin_order_models.py          # AdminOrderData, AdminOrderProduct
```

### Fixture

`admin_panel` fixture dodany do `qa/e2e/netcorner/conftest.py`:
```python
@pytest.fixture(scope="function")
def admin_panel(page, runtime_env) -> AdminWrappers
```

### URL admina

- Pattern: `https://admin-{host}.netcorner.pl/admin.php`
- Dla `komputronik-galak`: `https://admin-galak.test.netcorner.pl/admin.php`
- Lokatory potwierdzone live na środowisku testowym (2026-05-14).

### Zakres minimum (Faza 4) — DONE ✅

- [x] Login + obsługa context selector
- [x] Wyszukanie zamówienia po numerze (`AdminOrdersPage.open_order`)
- [x] Odczyt danych zamówienia: nabywca, odbiorca, NIP, ceny, status, produkty
- [x] `AdminWrappers.assert_order_details` z asercjami NIP / ceny / statusu / nabywcy
- [x] Zmiana statusu zamówienia (`AdminOrderDetailPage.change_status`)

### Zakres rozszerzony (Fazy 5-6) — TODO

- [ ] `AdminCartOfferPage` — tworzenie oferty koszykowej
- [ ] `AdminOzoPage` — reset liczników OZO
- [ ] `AdminPromoCodePage` — kody promocyjne
- [ ] `AdminEmployeeProgramPage` — program pracowniczy

## Success Criteria

### Funkcjonalny zakres minimum (odblokowanie Fazy 4)

#### Logowanie do admina
- Login + hasło → panel admina
- Metoda: `AdminLoginPage.login(username, password)`

#### Zarządzanie zamówieniami
- Wyszukanie zamówienia po numerze → `AdminOrdersPage.find_order(order_number)`
- Odczyt danych zamówienia:
  - dane nabywcy (imię, nazwisko, firma, NIP, adres)
  - dane odbiorcy
  - cena zamówienia (suma, wysyłka)
  - status zamówienia
  - lista produktów z cenami i ilościami
- Metoda: `AdminOrderDetailPage.get_order_data() -> AdminOrderData`

#### Weryfikacja zamówienia (odpowiednik `assert_admin_order_details`)
- Porównanie danych z TYP z danymi w adminie
- Metoda: `AdminWrappers.assert_order_details(order_number, expected_data)`

### Funkcjonalny zakres rozszerzony (odblokowanie Faz 5-6)

#### Zmiana statusu zamówienia
- Wybór statusu z listy → zapis → `AdminOrderDetailPage.change_status(status_id)`

#### Tworzenie oferty koszykowej
- Formularz + wysyłka do klienta → `AdminCartOfferPage.create_offer(data)`, `send_to_customer(email)`
- Pobieranie URL oferty → `AdminCartOfferPage.get_offer_url() -> str`

#### Reset liczników OZO
- Zerowanie licznika sprzedanych/pozostałych → `AdminOzoPage.reset_ozo_sales(product_id)`

#### Konfiguracja kodów pocztowych (dla TestOrderMatrixVsList)
- Ustawianie wymuszonych kodów pocztowych → `AdminConfigPage.enforce_postcode(postcode)`

#### Tworzenie kodów promocyjnych (dla PromotionsTestsNUXT)
- Nowy promo code + parametry → `AdminPromoCodePage.create_promo_code(data)`

#### Program pracowniczy (dla EmployeeProgramTestsNUXT)
- Tworzenie kodu pracowniczego SMS/QR → `AdminEmployeeProgramPage.create_code(data)`

## Proponowana architektura

```
qa/e2e/netcorner/nuxt/pl/lib/
├── page_objects/
│   └── pages/
│       └── admin/
│           ├── __init__.py
│           ├── admin_login_page.py          # logowanie do panelu
│           ├── admin_orders_page.py         # lista zamówień + wyszukiwanie
│           ├── admin_order_detail_page.py   # szczegóły zamówienia + zmiana statusu
│           ├── admin_cart_offer_page.py     # oferty koszykowe
│           ├── admin_ozo_page.py            # zarządzanie OZO
│           ├── admin_config_page.py         # konfiguracja sklepu
│           └── admin_promo_code_page.py     # kody promocyjne
└── flows/
    └── admin_wrappers.py                   # AdminWrappers — orchestration layer
```

### Modele danych

```python
# nowy plik: lib/test_data/orders/admin_order_models.py
@dataclass(frozen=True)
class AdminOrderData:
    order_number: str
    status: str
    summary_price: Decimal
    shipping_price: Decimal
    purchaser_data: list[str]   # imię, nazwisko, NIP, adres etc.
    products: list[AdminOrderProduct]

@dataclass(frozen=True)
class AdminOrderProduct:
    name: str
    quantity: int
    price: Decimal
```

## Wytyczne implementacji

1. Zachować architekturę page objects: ROOT_SELECTOR, lokatory w `__init__`, intent API
2. `AdminLoginPage` — singleton per session, jeden login na całą sesję testową
3. URL admina: `runtime_env.base_url.replace("//", "//admin.")` lub z settings
4. Używać `step_context()` z `qa.e2e.netcorner.lib.step_api`
5. `AdminWrappers` — analogiczny do `CartAndCheckoutWrappers` (przyjmuje `page, context, runtime_env`)
6. Wszystkie asercje w testach, nie w `AdminWrappers` (wrapper zwraca `AdminOrderData`)

## Success Criteria

### Automated Verification
- [ ] `make verify-scenarios` przechodzi po dodaniu admin page objects
- [ ] `pytest qa/e2e/netcorner/nuxt/pl/tests/tests_orders/ --collect-only` zbiera testy
- [ ] Testy Fazy 4 przechodzą na środowisku testowym

### Manual Verification
- [ ] `AdminWrappers.assert_order_details` poprawnie weryfikuje dane zamówienia z TYP
- [ ] Zmiana statusu w adminie widoczna na koncie klienta (dla TestOrderStatuses)
- [ ] Tworzenie oferty koszykowej + URL z maila == URL z admina (dla TestOrderCartOffer)

## Odwołania

- Selenium reference: `nc-functional-tests-py/TestCases/NetCornerProducts/admin_panel/Lib/PageObjects/`
- Plan sprintów: `thoughts/selenium_migration/plan.md` — Sprint 3
- Testy blokowane: `thoughts/selenium_migration/migration_todo.md` — Fazy 4 i 5
- Kontrakt page objects: `docs/E2E_PAGE_OBJECT_CONTRACT.md`
