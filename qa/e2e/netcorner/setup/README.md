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

## Uruchamianie

Zbiorczy target setupów:

```bash
make test-setup
```

## Kiedy uruchamiać

Setup `test-setup` powinien być odpalony **na każdej nowej testówce** (świeże środowisko / odtworzone dane),
zanim uruchomione zostaną testy E2E zależne od danych promocyjnych, indeksu i kupowalności produktów.

Rekomendowana kolejność logiczna (pokrycie SetUpNUXT):
1. promotions service,
2. promo codes,
3. recompute products,
4. promotions sezam,
5. index products.
