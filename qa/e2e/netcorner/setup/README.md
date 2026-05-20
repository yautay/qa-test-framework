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

Kolejność wymuszana jest markerami `@pytest.mark.order(...)` (plugin `pytest-order`).
