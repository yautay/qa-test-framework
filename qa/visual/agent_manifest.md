# VRT Agent Manifest (No Repo Scan)

Cel: ograniczyc zuzycie tokenow i wymusic prace tylko na plikach niezbednych do generowania testow VRT dla nowych podstron.

## Read Only This (in order)

1. `framework/visual/visual_suite.py`
2. `framework/visual/scenario_loader.py`
3. `framework/visual/models.py` (sekcje: `VisualScenario`, `VisualCapture`, `VisualMask`, `VisualThresholds`)
4. `qa/visual/netcorner/nuxt/pl/listings/test_listings_visual.py`
5. `qa/visual/netcorner/nuxt/pl/listings/*.json`
6. `qa/visual/netcorner/nuxt/pl/product_page/*.json`
7. `qa/visual/netcorner/nuxt/pl/hero_page/vrt-netcorner-nuxt-pl-hero-homepage-no-cache.json`
8. `settings.py` (tylko `visual_viewport_presets`)
9. `qa/visual/netcorner/nuxt/pl/_inputs/new_urls.json` (lista URL wejscia)

## Hard Rules

- Nie skanuj calego repo (`glob`/`grep`) poza sciezkami z listy powyzej.
- Nie czytaj `trash/*` jako zrodla prawdy.
- Nie modyfikuj `hero_page` dla `/` i `/?a=0`, chyba ze zadanie wprost tego wymaga.
- Dla nowych plikow JSON trzymaj max 10 obiektow na plik (`-part-01`, `-part-02`, ...).
- Kazdy scenariusz musi miec unikalne `id`.
- Nie tworz masowo komponentow per URL. Komponenty tylko reprezentatywne (po 1 na suite).

## Minimal Scenario Contract

Kazdy scenariusz JSON musi zawierac:

- `id`
- `name`
- `suite_id`
- `target_url`
- `compare_mode: "hybrid"`
- `capture`
- `mask`
- `thresholds` (`pixel_max: 0.01`, `lpips_max: 0.12`, `dists_max: 0.12`)

Wymagane placeholdery:

- `capture.locator: "[data-name='replace-capture-selector']"` tylko dla `type: element`
- `mask.locators` zawiera `"[data-name='replace-mask-selector']"` (Playwright selector string; CSS nadal wspierany)
- `mask.color: "#00FF00"`

## Suggested Agent Invocation

Uzyj tego polecenia jako prompt startowy dla agenta:

```text
Pracuj tylko na plikach z qa/visual/netcorner/nuxt/pl/agent_manifest.md.
Nie skanuj repo poza wskazanymi sciezkami.
Wczytaj URL-e z qa/visual/netcorner/nuxt/pl/_inputs/new_urls.json.
Wygeneruj testy VRT dla nowych podstron zgodnie z obecnym schematem suite pl.
```
