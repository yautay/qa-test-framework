# Visual Tests (`qa/visual`)

Ten dokument opisuje jak dodawac nowe przypadki visual, jakie pola JSON sa dozwolone oraz jak definiowac kroki funkcjonalne przed capture.

## Szybki start

1. Dodaj nowy plik `*.json` do katalogu suite, np.:
   - `qa/visual/netcorner/nuxt/pl/hero_page/`
   - `qa/visual/netcorner/nuxt/pl/layers/`
   - `qa/visual/netcorner/nuxt/pl/listings/`
   - `qa/visual/netcorner/nuxt/pl/product_page/`
2. Upewnij sie, ze `id` jest unikalne globalnie.
3. Uruchom test visual:
   - `make test-visual`
   - albo `python -m pytest -m visual -q`

## Struktura scenariusza JSON

Minimalny przyklad:

```json
{
  "id": "vrt-netcorner-nuxt-pl-layers-login",
  "name": "Login page visual",
  "suite_id": "netcorner/nuxt/pl/layers",
  "target_url": "/login",
  "compare_mode": "hybrid",
  "capture": {
    "type": "page",
    "full_page": true
  },
  "thresholds": {
    "pixel_max": 0.01,
    "lpips_max": 0.12,
    "dists_max": 0.12
  },
  "steps": []
}
```

## Dozwolone pola i znaczenie

- `id` (string, wymagane)
  - Unikalny identyfikator scenariusza.
- `name` (string, wymagane)
  - Nazwa czytelna dla raportu.
- `suite_id` (string, wymagane)
  - Logical suite, np. `netcorner/nuxt/pl/layers`.
- `target_url` (string, wymagane)
  - URL relatywny (`/login`) albo absolutny (`https://...`).
  - Dla URL relatywnego wymagany jest poprawny `BASE_URL`.
- `compare_mode` (string, wymagane)
  - Dozwolone: `pixel`, `hybrid`.
- `viewport` (opcjonalne)
  - String lub lista stringow (np. `["mobile", "fhd"]`).
  - Dozwolone presety: `mobile`, `tablet`, `fhd`, `2k`, `4k`.
  - Gdy brak, uzywany jest viewport z CLI (`--viewport`).
- `capture` (opcjonalne, obiekt)
  - `type`: `page` | `viewport` | `element` (domyslnie `page`)
  - `full_page`: bool (domyslnie `true`)
  - `selector`: wymagany tylko dla `type = "element"`
- `thresholds` (opcjonalne, obiekt)
  - `pixel_max`, `lpips_max`, `dists_max` (number)
  - opcjonalnie:
    - `pixel_uncertain_delta`
    - `lpips_uncertain_delta`
    - `dists_uncertain_delta`
- `mask` (opcjonalne, obiekt)
  - `selectors`: lista CSS selectorow do zamaskowania
  - `color`: `#RRGGBB` (np. `#00FF00`)
- `steps` (opcjonalne, lista)
  - Kroki funkcjonalne wykonywane po wejsciu na `target_url`, przed screenshotem.
- `perceptual_required` (opcjonalne, bool)
  - Dodatkowy znacznik do pipeline perceptual.

Uwaga:
- Nieznane pola JSON sa ignorowane przez runner (ale zostaja zapisane w `raw_definition` w metadanych raportu).

## Kroki funkcjonalne (`steps`)

Kazdy krok ma format:

```json
{
  "action": "click|fill|wait_for_selector|wait_for|wait|wait_for_timeout|goto",
  "selector": "",
  "value": "",
  "url": "",
  "timeout_ms": 5000
}
```

### Obslugiwane `action`

- `click`
  - wymagane: `selector`
- `fill`
  - wymagane: `selector`, `value`
- `wait_for_selector` (alias: `wait_for`)
  - wymagane: `selector`
- `wait` (alias: `wait_for_timeout`)
  - uzywa `timeout_ms`
- `goto`
  - wymagane: `url` albo `value` (traktowane jako URL)

Przyklad:

```json
"steps": [
  { "action": "click", "selector": "[data-name='loginDialogTrigger']" },
  { "action": "fill", "selector": "#loginEmail", "value": "user@example.com" },
  { "action": "fill", "selector": "#loginPassword", "value": "secret" },
  { "action": "click", "selector": "button:has-text('Zaloguj sie')" },
  { "action": "wait_for_selector", "selector": "[href='/customer/account/']", "timeout_ms": 10000 },
  { "action": "wait", "timeout_ms": 500 }
]
```

## Zachowanie runtime

- Dla `capture.full_page = true` runner wykonuje dodatkowa stabilizacje przed screenshotem:
  - best-effort `networkidle`,
  - scroll dol/gora (lazy-load),
  - krotki wait na obrazy i fonty.
- Dla `full_page = false` stabilizacja lazy-load nie jest wymuszana.
- Nawigacja (`target_url` i step `goto`) failuje test przy bledach HTTP:
  - brak odpowiedzi (`None`) -> fail,
  - status `>= 400` (np. 404/500) -> fail.

## Dobre praktyki

- Uzywaj stabilnych selectorow (`data-*`) zamiast klas stylujacych.
- Maskuj elementy dynamiczne (cookie, bannery, personalizacja, timery).
- Przy asynchronicznym UI dodaj `wait_for_selector` zamiast dlugiego `wait`.
- Dla jednego `id` trzymaj jedna odpowiedzialnosc (jedna scena UI).

## Jak dodac nowy przypadek krok po kroku

1. Skopiuj najblizszy istniejacy JSON z tego samego katalogu suite.
2. Zmien `id`, `name`, `target_url`.
3. Ustaw `capture` (`full_page = true` jesli zalezy Ci na calej stronie).
4. Dodaj lub zmodyfikuj `mask`.
5. Dodaj `steps` (jesli potrzebne).
6. Uruchom:
   - `python -m pytest -m visual -k <fragment_id> -q`
7. Sprawdz wynik w `artifacts/<run_id>/visual/` i raporcie UI (`make report-serve`).

## Kroki funkcjonalne z Page Object (plan)

Docelowo mozna dodac `precondition.flow` mapowany na funkcje Python z uzyciem Page Object z E2E (np. `login_client`).

Ten mechanizm nie jest jeszcze aktywny w runnerze visual. Aktualnie wspierane sa kroki przez `steps`.
