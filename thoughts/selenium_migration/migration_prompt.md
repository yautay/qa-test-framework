---
date: 2026-05-12T00:00:00+02:00
git_commit: ee7e62b2ad3517ed49a183807d9a91d284a259de
branch: feature/NN-24016-ai-w-pisaniu-testow-e2e
repository: qa-test-netquarner
topic: "Gotowy prompt AI do migracji testów Selenium → Playwright (netcorner nuxt pl)"
tags: [prompt, migration, selenium, playwright, ai, orders, e2e]
last_updated: 2026-05-12
---

# Prompt: Migracja testów Selenium → Playwright

Skopiuj poniższy blok i użyj go jako instrukcji startowej przy każdej nowej sesji migracji.

---

## Kontekst repozytoriów

**Stare repo (Selenium/unittest):** `nc-functional-tests-py`
- Testy: `TestCases/NetCornerProducts/pl_komputronik_nuxt/Test/<SuiteName>/`
- Page objects: `TestCases/NetCornerProducts/pl_komputronik_nuxt/Lib/PageObjects/`
- Dane testowe: `TestData/pl_komputronik_nuxt/`
- Admin panel: `TestCases/NetCornerProducts/admin_panel/Lib/PageObjects/`
- Mailhog: `TestCases/NetCornerProducts/mailhog_panel/Lib/PageObjects/MailhogObjects.py`
- Wzorzec: `unittest` + `ddt` + `@data(DictDP(...))` + `KomputronikTestSetupNuxt`

**Nowe repo (Playwright/pytest):** `qa-test-netquarner`
- Testy: `qa/e2e/netcorner/nuxt/pl/tests/`
- Page objects: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/`
- Wrappers/Flows: `qa/e2e/netcorner/nuxt/pl/lib/flows/`
- Dane testowe: `qa/e2e/netcorner/nuxt/pl/lib/test_data/`
- Mailhog (już istnieje): `qa/e2e/netcorner/mailhog/lib/`
- Środowisko testowe: `https://komputronik-galak.test.netcorner.pl/`

## Dokumenty do przeczytania PRZED implementacją

1. `AGENTS.md` — Python 3.13, makefile, zakazy
2. `docs/E2E_PAGE_OBJECT_CONTRACT.md` — kontrakt page objects (ROOT_SELECTOR, no-fallback)
3. `qa/e2e/netcorner/nuxt/pl/lib/page_objects/AGENTS.md` — zasady scope/root
4. `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/AGENTS.md` — intent API
5. `thoughts/selenium_migration/research.md` — analiza infrastruktury obu repozytoriów
6. `thoughts/selenium_migration/plan.md` — plan sprintów i zależności
7. `thoughts/selenium_migration/migration_todo.md` — lista wszystkich testów do migracji

## Istniejąca infrastruktura Playwright (nie duplikować)

### Flows / Wrappers
| Klasa | Plik | Funkcja |
|---|---|---|
| `SelectProductWrappers` | `lib/flows/select_product_wrappers.py` | Wybór produktu z listingu → koszyk |
| `CartAndCheckoutWrappers` | `lib/flows/cart_and_checkout_wrappers.py` | Koszyk → pełny checkout → TYP |
| `ClientWrappers` | `lib/flows/client_wrappers.py` | Rejestracja, wylogowanie |
| `MailInboxService` | `qa/e2e/netcorner/mailhog/lib/flows/inbox_flow.py` | Mailhog/Roundcube: link z maila po wzorcu tematu |

### MailInboxService — dostępne metody
```python
mail_inbox.get_password_reset_link(context=context, recipient=email)
mail_inbox.get_order_mail_link(context=context, recipient=email, shop_host=host, order_number=nr)
mail_inbox.get_link_from_subject(context=context, recipient=email, subject=MailSubjectPattern(...), link_regex=r"...")
```
Fixture: `mail_inbox` (z `qa/e2e/netcorner/conftest.py`)

### MailSubjects — dostępne wzorce
```python
MailSubjects.PASSWORD_RESET
MailSubjects.LOGIN
MailSubjects.NEW_USER_REGISTERED
MailSubjects.ORDER_PROBLEM
MailSubjects.order_shop_number(shop_host, order_number)   # mail do partnera/sklepu
MailSubjects.order_summary_komputronik(order_number)      # mail do klienta
```

### Typy dostawy i generatory danych
```python
# checkout_data_models.py
DeliveryTypes.INPOST / DHL_POP / COURIER_SERVICE / STORE_PICKUP

# checkouts_generators.py
checkout_delivery_cases()          # 8 przypadków (4 typy × prywatny/firma)
private_person_checkout_purchaser()
company_checkout_purchaser()       # z tax_identification_number (NIP)

# client_generators.py
auth_session_cases()               # logged_in + anonymous
auth_session_not_registered()      # anonymous only
auth_session_logged()              # logged_in only
ClientDataBuilder().with_required_terms().build()
```

### Strony i komponenty
```python
# Pages
HomePage, ListingPage, ProductPage, CartPage, CheckoutPage
MyAccountPage, MyAccountChangePasswordPage, RegisterPage

# Overlays (checkout)
Overlays(page).checkout_courier_receiver
Overlays(page).checkout_inpost_receiver
Overlays(page).checkout_dhl_pop_receiver
Overlays(page).checkout_storehouse_receiver
Overlays(page).checkout_purchaser
```

## Wzorzec nowego testu

```python
from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import CheckoutDeliveryCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import checkout_delivery_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import auth_session_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_aviable_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.orders]   # markery obligatoryjne


@allure.feature("Proces zakupowy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda c: c.case_id)
@pytest.mark.parametrize("delivery_case", checkout_delivery_cases(), ids=lambda c: c.case_id)
@pytest.mark.scenario("Opis scenariusza po polsku")
def test_nazwa_testu(page, context, runtime_env, auth_case: AuthSessionCase, delivery_case: CheckoutDeliveryCase):
    # 1. Opcjonalna rejestracja
    user_data = None
    if auth_case.authenticated:
        user_data = ClientDataBuilder().with_required_terms().build()
        assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), \
            "Użytkownik nie został zarejestrowany."

    # 2. Wybór produktu
    listings_data = first_aviable_laptop_case()
    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected is not None, "Nie udało się wybrać produktu."

    # 3. Dump danych (obowiązkowy)
    dump_data(auth_case=auth_case, delivery_case=delivery_case, user_data=user_data)

    # 4. Checkout
    wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    wrappers.process_cart()
    result = wrappers.process_checkout(
        delivery_case.delivery_type,
        delivery_case.delivery_objects,
        delivery_case.purchaser_objects,
        delivery_case.payment_objects,
    )

    # 5. Asercje (bezpośrednio w teście, po polsku)
    assert result.typ_summary_data.order_number.strip(), \
        "Nie potwierdzono złożenia zamówienia: brak numeru zamówienia."

    # TODO: weryfikacja w adminie po zbudowaniu admin page objects (Sprint 3)
```

## Proces migracji krok po kroku

### 1. Przeanalizuj test źródłowy
- Zidentyfikuj dane testowe (`test_data["..."]`)
- Zidentyfikuj używane page objects (`Page.*`)
- Wypisz asercje (co jest faktycznie sprawdzane)
- Sprawdź zależności: admin? mailhog? konfiguracja przed testem?

### 2. Sprawdź co istnieje w Playwright repo
- Czy wrapper/flow już coś pokrywa?
- Czy page object już istnieje?
- Czy modele danych wystarczają?

### 3. Zidentyfikuj luki
- Nowy wrapper/flow (jeśli przepływ jest nowy)
- Nowy page object / komponent (jeśli nowy element UI)
- Nowe modele danych (jeśli nowe dane testowe)

### 4. Zbuduj bottom-up
```
test_data/ models → test_data/ generators → page_objects/ → flows/ → test file
```

### 5. Nowy page object (checklist)
- [ ] Dziedziczy z lokalnego `BasePage` lub `BaseComponent`
- [ ] Ma `ROOT_SELECTOR` jako class constant
- [ ] Lokatory inicjalizowane w `__init__` jako `self.__name = self.root.get_by_*` lub `self.find(...)`
- [ ] Metody mają nazwy intent-driven (`click_add_to_cart`, `get_order_status`, nie `find_button`)
- [ ] Używa `step_context()` z `qa.e2e.netcorner.lib.step_api` (nie `allure.step`)
- [ ] Nie ujawnia lokatorów na zewnątrz
- [ ] Nie zawiera asercji testowych

### 6. Nowy model danych (checklist)
- [ ] Dataclass (preferably `frozen=True`)
- [ ] Ma `case_id: str`
- [ ] Builder pattern dla złożonych obiektów
- [ ] Generator funkcji zwracający `list[...]` dla parametryzacji

### 7. Weryfikacja po implementacji
```bash
# Sprawdź czy pytest może zebrać testy
pytest qa/e2e/netcorner/nuxt/pl/tests/ --collect-only -q

# Pełna weryfikacja
make verify-scenarios
```

## Zasady których NIE łamać

| Zakaz | Dlaczego |
|---|---|
| Fallback chains (`try/except` na lokatory) | Ukrywa dryft selectorów |
| `page.locator(...)` wewnątrz komponentu | Naruszenie boundary root |
| `time.sleep()` | Używaj `wait_for*` |
| Lokatory w osobnych plikach | Kontrakt: lokatory w konstruktorze klasy |
| Asercje w page objects | Asercje tylko w teście |
| `allure.step()` bezpośrednio | Używaj `step_context()` |
| Import z Selenium repo | Absolutnie niedozwolone |
| Unittest style (`setUp/tearDown`) | Wszystko przez pytest fixtures |

## Obsługa admina i Mailhog w testach

### Gdy test Selenium wywołuje `AdminPageObjects`:
```python
# TODO (Sprint 3): weryfikacja w adminie po zbudowaniu admin page objects
# Selenium: Page.AdminPageObjects(self.driver).assert_admin_order_details(self.admin_url, test_data)
# Playwright: AdminWrappers(page, context, runtime_env).assert_order_details(order_number, expected)
```

### Gdy test Selenium wywołuje `MailhogObject`:
```python
# Dostępne już TERAZ przez MailInboxService:
link = mail_inbox.get_link_from_subject(
    context=context,
    recipient=user_data.email,
    subject=MailSubjects.order_summary_komputronik(order_number),
    link_regex=r"https?://[^\s]*(order|zamow)[^\s]*",
)

# BRAKUJE (Sprint 4): count_mails_matching, has_mail_with_subject_containing
# TODO (Sprint 4): rozszerzyć MailInboxService o metody zliczania maili
```

## Mailhog — co już działa, czego brakuje

### Działa (użyj teraz)
- Pobieranie linku z maila po wzorcu tematu → `get_link_from_subject`
- Reset hasła → `get_password_reset_link`
- Potwierdzenie zamówienia → `get_order_mail_link`
- Własny `MailSubjectPattern` → `get_link_from_subject(..., subject=MailSubjectPattern(key=..., regex=..., description=...))`

### Brakuje (Sprint 4)
- `count_mails_matching(context, recipient, subject, timeout_ms)` — zliczanie maili
- `has_mail_with_subject_containing(context, recipient, text)` — temat zawiera tekst
- `MailSubjects.ORDER_STATUS_CHANGED` — powiadomienia o zmianach statusu
- `MailSubjects.CART_OFFER` — oferta koszykowa
- `MailSubjects.PARTNER_STOREHOUSE_ORDER` — mail do partnera

## Metryki gotowości (co oznaczają gwiazdki w migration_todo.md)

| Oznaczenie | Znaczenie |
|---|---|
| `[x]` | Test zmigrowany i gotowy |
| `[ ]` | Do zrobienia |
| `🔴 admin` | Blokowany przez brak admin panel page objects |
| `🟡 mailhog` | Blokowany przez brakujące metody w MailInboxService |
| `🔵 new-po` | Wymaga nowych page objects (nie admin) |
| `⚪ covered` | Pokryty przez inny istniejący test |
