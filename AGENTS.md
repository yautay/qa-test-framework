# AGENTS

Ten plik opisuje oczekiwany sposob pracy asystentow AI w tym repozytorium.

## Szybki kontekst repozytorium

- Nazwa: netQArner Test Framework
- Cel: framework QA do testow E2E, API i wizualnych.
- Dokumentacja uzytkownika: `README.md`
- Dokumentacja dla dev: `README-DEV.md`

## Struktura katalogow

- `qa/` - aktywne testy (E2E, API, visual)
- `framework/` - runtime, raportowanie, artefakty, runner wizualny
- `tools/` - skrypty pomocnicze i narzedzia
- `docs/` - dokumentacja procesow i integracji

## Jak pracowac

1. Zaczynaj od `README.md`, a gdy dotykasz frameworka - od `README-DEV.md`.
2. Trzymaj sie istniejacych konwencji plikow i stylu w danym katalogu.
3. Nie zmieniaj konfiguracji CI ani narzedzi bez wyraznej prosby.
4. Nie usuwaj danych, logow ani artefaktow, jezeli nie jest to wymagane.
5. Minimalizuj zakres zmian i unikaj refactorow bez uzasadnienia.
6. Prompt dla automatycznego CR: `docs/CR_AUDIT_PROMPT.md`.
7. Dla automatycznego generowania testow E2E stosuj wytyczne z `docs/ai-agents/e2e/`.

## Standardy kodowania

- Trzymaj sie istniejacego stylu w danym katalogu i pliku.
- Unikaj zmian formatowania niezwiazanych z celem zadania.
- Preferuj male, czytelne zmiany zamiast szerokich refactorow.
- Komentarze dodawaj tylko, gdy logika nie jest oczywista.

## Najczestsze komendy

Uruchamianie testow:

```bash
make test-e2e
make test-visual
make test-aso
```

Kontrola jakosci:

```bash
make lint
make format-check
make typecheck
make security
make check
```

Walidacja konfiguracji i discovery:

```bash
make verify-scenarios
make verify-discovery
python -m pytest --collect-only -q
python framework/pytest_discovery_guard.py
```

Raporty i baseline (visual):

```bash
make report-serve
make debug-minio-up
make debug-minio-down
```

Sprzatanie artefaktow:

```bash
make clean
make clean-artifacts
make clean-artifacts-older DAYS=14
```

## Konfiguracja

- Glowne ustawienia lokalne: `settings_cli.py`
- Domyslne wartosci kompatybilnosci: `settings.py`
- Opcjonalne nadpisania: `.env` (z `.env.example`)

## Wazne wskazowki dla zmian w testach

- Przy testach wizualnych sprawdz katalogi w `qa/visual/`.
- Przy zmianach raportowania sprawdz dokumenty w `docs/`.
- Jezeli modyfikujesz scenariusze, uruchom `make verify-scenarios`.
- Jezeli dotykasz discovery testow, uruchom `make verify-discovery`.

## Zasady pracy z testami wizualnymi

- Bazuj na dokumentacji: `docs/VISUAL_BASELINE_APPROVAL_FLOW.md` i `qa/visual/README.md`.
- Nie usuwaj baseline ani artefaktow bez wyraznej prosby.
- Do lokalnej akceptacji baseline uzywaj raportu (`make report-serve`).
- Przy zmianach w narzedziach baseline zajrzyj do `tools/visual/README.md`.

## Zasady pracy z CI i raportowaniem

- Nie zmieniaj konfiguracji CI (`.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile`) bez wyraznej prosby.
- Zmiany w raportowaniu konsultuj z `docs/REPORTING_HTTP_INTEGRATION.md`.
- Zachowuj kompatybilnosc danych raportowych i metadanych runu.

## Workflow zmian w scenariuszach

- Po edycji scenariuszy uruchom `make verify-scenarios`.
- Jezeli zmieniasz discovery lub markerow, uruchom `make verify-discovery`.
- Sprawdz zgodnosc z `qa/visual/README.md` dla scenariuszy wizualnych.

## Zasady uruchamiania testow lokalnie

- Uzywaj Pythona 3.13 zgodnie z `pyproject.toml`.
- Uruchomione testy E2E/visual wymagaja instalacji Playwright: `python -m playwright install chromium`.
- Preferuj komendy `make test-e2e`, `make test-visual`, `make test-aso`.

## Raportowanie i artefakty

- Przewodnik artefaktow: `docs/ARTIFACTS.md`.
- Integracja raportowania: `docs/REPORTING_HTTP_INTEGRATION.md`.
- Zachowuj zgodnosc metadanych runu z obecnym formatem.

## Lokalnne hooki git

- Hook source: `tools/hooks/pre-commit-aso.sh`.
- Instalacja: `./tools/hooks/install-local-hooks.sh`.
- Hook uruchamia `make test-aso` przed commitem.

## Pomocniki zdalne/grid

```bash
make debug-remote-grid-up
make debug-remote-grid-down
```

## Macierz srodowisk i env

- Glowne zrodla ustawien: `settings_cli.py`, `settings.py`, `.env`.
- Routing targetu: `BASE_URL`, `BASE_URL_OVERRIDE`, `REFERENCE_HOST` i `--server-name`.
- Raportowanie: `REPORTING_*`.
- Visual/baseline/PMS: `VISUAL_*`, `VISUAL_MINIO_*`, `PMS_*`.
- Grid/runtime: `BROWSER`, `HEADLESS`, `IS_GRID_AVAILABLE`, `GRID_*`.

## Zasady komunikacji

- Odpowiedzi krotkie, konkretne, bez zbednych dygresji.
- Jezeli decyzja jest niejednoznaczna, proponuj domyslne rozwiazanie i uzasadnienie.
- Nie wykonuj destrukcyjnych polecen bez potwierdzenia uzytkownika.
