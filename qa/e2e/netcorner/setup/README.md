# Netcorner SetUp

Katalog `qa/e2e/netcorner/setup/` zawiera setupy środowiskowe wymagane przez testy E2E.

Zakres przeniesiony z Selenium SetUpNUXT:
- setup kodów promocyjnych,
- przeliczenie kupowalności produktów (save produktu),
- zapis istniejących promocji Sezam na produktach,
- indeksowanie produktów do search po kodach ERP,
- zapis promocji w promotion-service po ID.

Implementacja:
- `setup_data.py` — dane setupowe (promo IDs, domyślne kody promo),
- `setup_flows.py` — serwis `NetcornerSetupService` i obiektowe flow setupowe.

Uwagi dot. zakresu produktów:
- `test_setup_tests_promotions_sezam` obejmuje dedykowane produkty Sezam (`SEZAM_PRODUCT_CASES`),
- `test_setup_index_products` obejmuje pełny zbiór produktów setupowych (`RECOMPUTING_PRODUCT_PURCHASE_ELIGIBILITY_IDS`).

## Uruchamianie

Zbiorczy target setupów:

```bash
make test-setup
```

## Kiedy uruchamiać

Setup `test-setup` powinien być odpalony **na każdej nowej testówce** (świeże środowisko / odtworzone dane),
zanim uruchomione zostaną testy E2E zależne od danych promocyjnych, indeksu i kupowalności produktów.

Rekomendowana kolejność logiczna (pokrycie SetUpNUXT):
1. promotions sezam,
2. promotions service,
3. promo codes,
4. OZO (reset promocji + walidacja widgetu homepage),
5. recompute products,
6. index products.

Kolejnosc nie jest wymuszana globalnie przez pluginy kolejkowania.
Wymagana zaleznosc dla setupu jest realizowana technicznie:
- `test_setup_tests_promotions_service` zapisuje timestamp zakonczenia,
- `test_setup_tests_promo_codes` czeka minimum 120 sekund od tego momentu.

## Synchronizacja i opóźnienia

### Opóźnienie po zapisie promotion-service (120 s)

Po zapisaniu wszystkich promocji w promotion-service flow wykonuje stałe oczekiwanie
`_PROMOTION_SERVICE_ACTIVATION_WAIT_MS = 120_000` ms (`setup_flows.py`).

**Jest to celowe ograniczenie architektoniczne**, nie kompensacja flakiness:
promotion-service propaguje zmiany asynchronicznie i nie udostępnia sygnału gotowości
backendowej. `test_setup_tests_promo_codes` jawnie zależy od tego okna (czeka min. 120 s
od zakończenia zapisu promocji przed weryfikacją kodów).

Docelowa ścieżka poprawy: zastąpić stały sleep pollingiem warunku UI-side
(np. brak `.alert-danger` + widoczność zapisanej promocji na stronie sklepu)
przez `framework.polling.poll_until`, gdy pojawi się deterministyczny sygnał gotowości.
Do tego czasu stała musi pozostać bez zmian, a jej wartość nie powinna być skracana
bez weryfikacji zależności w `test_setup_tests_promo_codes`.
