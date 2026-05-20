# Visual JSON template for `layers`

Ten plik opisuje szablon `vrt-test-template.json` i wyjaśnia:
- które pola są **wymagane**,
- które są **opcjonalne**,
- co każde pole robi,
- kiedy warto go użyć.

## Pola wymagane

### `id`
- **Typ:** `string`
- **Wymagane:** tak
- **Co robi:** unikalny identyfikator scenariusza visual.
- **Uwagi:** powinien być unikalny globalnie, bo na jego podstawie powstają nazwy artefaktów i baseline'ów.

Przykład:

```json
"id": "vrt-netcorner-nuxt-pl-layers-login"
```

---

### `suite_id`
- **Typ:** `string`
- **Wymagane:** tak
- **Co robi:** logiczna ścieżka suite'a, używana do grupowania scenariuszy i baseline'ów.

Przykład:

```json
"suite_id": "netcorner/nuxt/pl/layers"
```

---

### `target_url`
- **Typ:** `string`
- **Wymagane:** tak
- **Co robi:** adres strony, na którą runner ma wejść przed wykonaniem kroków i capture.
- **Może być:**
  - relatywny, np. `"/login"`
  - absolutny, np. `"https://example.com/login"`

Przykład:

```json
"target_url": "/login"
```

---

### `compare_mode`
- **Typ:** `string`
- **Wymagane:** tak
- **Dozwolone wartości:** `"pixel"`, `"hybrid"`
- **Co robi:** określa tryb porównania z baseline'em.
  - `pixel` – porównanie pikselowe
  - `hybrid` – tryb hybrydowy używany przez framework visual

Przykład:

```json
"compare_mode": "hybrid"
```

## Pola opcjonalne

### `name`
- **Typ:** `string`
- **Wymagane:** nie
- **Co robi:** czytelna nazwa scenariusza w raportach.
- **Jeśli brak:** framework użyje wartości z `id`.

---

### `viewport`
- **Typ:** `string` lub `string[]`
- **Wymagane:** nie
- **Co robi:** pozwala uruchomić ten sam scenariusz na konkretnych presetach viewportu.
- **Dozwolone presety:** `mobile`, `tablet`, `fhd`, `2k`, `4k`
- **Jeśli brak:** użyty zostanie viewport z CLI/test runtime.

Przykład:

```json
"viewport": ["mobile", "tablet", "fhd"]
```

---

## Obiekt `capture`

- **Typ:** `object`
- **Wymagane:** nie, ale praktycznie prawie zawsze warto go jawnie podać
- **Co robi:** definiuje, co dokładnie ma zostać zrzutowane do screenshotu

### `capture.type`
- **Typ:** `string`
- **Wymagane:** nie
- **Dozwolone wartości:** `"page"`, `"viewport"`, `"element"`
- **Domyślnie:** `"page"`
- **Co robi:**
  - `page` – screenshot strony
  - `viewport` – screenshot aktualnego viewportu
  - `element` – screenshot konkretnego elementu

### `capture.locator`
- **Typ:** `string`
- **Wymagane:** tak dla `capture.type = "element"`
- **Co robi:** locator Playwrighta wskazujący element do capture.
- **Uwaga:** aktualnie używamy **tylko `locator`**, nie `selector`.

### `capture.full_page`
- **Typ:** `boolean`
- **Wymagane:** nie
- **Domyślnie:** `true`
- **Co robi:**
  - `true` – screenshot całej strony
  - `false` – screenshot aktualnego widocznego obszaru lub elementu

Przykład:

```json
"capture": {
  "type": "element",
  "locator": "[data-name='loginDialog']",
  "full_page": false
}
```

---

## Obiekt `mask`

- **Typ:** `object`
- **Wymagane:** nie
- **Co robi:** maskuje dynamiczne elementy, które mogłyby powodować flaky diffy

### `mask.locators`
- **Typ:** `string[]`
- **Wymagane:** nie
- **Co robi:** lista locatorów Playwrighta/CSS, które zostaną zamaskowane na screenshocie.
- **Kiedy używać:** dla banerów, timerów, dynamicznych cen, carouseli, personalizacji, cookie bannerów itp.

### `mask.color`
- **Typ:** `string`
- **Wymagane:** nie
- **Format:** `#RRGGBB`
- **Domyślnie:** `#DDF527`
- **Co robi:** kolor nakładanej maski.

Przykład:

```json
"mask": {
  "locators": [
    ".cookie-banner",
    "[data-testid='dynamic-banner']"
  ],
  "color": "#DDF527"
}
```

---

## Obiekt `thresholds`

- **Typ:** `object`
- **Wymagane:** nie
- **Co robi:** definiuje progi akceptowalnych różnic między aktualnym screenshotem a baseline'em

### Podstawowe pola
- `pixel_max` – maksymalny dopuszczalny pixel diff
- `lpips_max` – maksymalny dopuszczalny LPIPS
- `dists_max` – maksymalny dopuszczalny DISTS

### Dodatkowe pola
- `pixel_uncertain_delta`
- `lpips_uncertain_delta`
- `dists_uncertain_delta`
  - używane do strefy niepewności (`uncertain`)
- `shift_compensation_y_px`
  - kompensacja pionowego przesunięcia layoutu

Przykład:

```json
"thresholds": {
  "pixel_max": 0.01,
  "lpips_max": 0.12,
  "dists_max": 0.12,
  "pixel_uncertain_delta": 0.02,
  "lpips_uncertain_delta": 0.02,
  "dists_uncertain_delta": 0.02,
  "shift_compensation_y_px": 100
}
```

---

## `steps`

- **Typ:** `array`
- **Wymagane:** nie
- **Co robi:** lista kroków wykonywanych po wejściu na `target_url`, ale przed screenshotem

Każdy step może zawierać:
- `action`
- `selector`
- `value`
- `url`
- `timeout_ms`

### Obsługiwane akcje
- `click`
- `fill`
- `wait_for_selector`
- `wait_for`
- `wait`
- `wait_for_timeout`
- `goto`

### Kiedy używać
- otwieranie modali / layerów
- wpisywanie danych do formularzy
- czekanie aż UI się ustabilizuje
- dodatkowa nawigacja przed capture

Przykład:

```json
"steps": [
  {
    "action": "click",
    "selector": "[data-name='open-layer']",
    "timeout_ms": 5000
  },
  {
    "action": "wait_for_selector",
    "selector": "[data-name='layer-content']",
    "timeout_ms": 10000
  }
]
```

---

## `cookies`

- **Typ:** `array`
- **Wymagane:** nie
- **Co robi:** pozwala ustawić cookies przed wykonaniem scenariusza
- **Obsługiwane pola w cookie:**
  - `name`
  - `value`
- **Uwaga:** domain i path są ustawiane przez runtime

Przykład:

```json
"cookies": [
  {
    "name": "kt-color-mode",
    "value": "yellow-black"
  }
]
```

---

## `perceptual_required`

- **Typ:** `boolean`
- **Wymagane:** nie
- **Domyślnie:** `false`
- **Co robi:** dodatkowa flaga zapisywana w modelu scenariusza dla pipeline perceptual

Przykład:

```json
"perceptual_required": false
```

---

## Dodatkowe uwagi praktyczne

1. Używaj stabilnych locatorów, najlepiej `data-*`.
2. Dynamiczne elementy zawsze staraj się maskować.
3. Jeśli test otwiera modal/layer, zwykle warto dodać `steps` zamiast liczyć na sam stan strony.
4. Jeśli tworzysz element capture, ustawiaj `full_page: false`.
5. `selector` jako alias jest obsługiwany przez loader w niektórych miejscach, ale w nowych testach trzymajmy się tylko **`locator`** i **`locators`**.
