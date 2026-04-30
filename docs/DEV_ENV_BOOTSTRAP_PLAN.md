# DEV Environment Bootstrap Plan

## Cel

Przygotowac powtarzalny bootstrap srodowiska developerskiego dla repo `netQArner` z oficjalnym workflow:

- Windows jako host dla `VSCode`
- `WSL2` jako glowne srodowisko uruchomieniowe dla Python/Node/testow
- osobny, uproszczony bootstrap hosta Windows
- osobny bootstrap srodowiska dev w WSL2

## Zalozenia

- `WSL2`, `Git` i `VSCode` sa instalowane recznie i nie sa instalowane przez skrypty repo.
- Skrypty moga jedynie sprawdzac ich dostepnosc i podawac czytelny komunikat, jesli czegos brakuje.
- Bootstrap ma byc uruchamiany z katalogu repo i dzialac idempotentnie.
- Repo ma zostac przygotowane pod prace w `VSCode` z wymaganymi rozszerzeniami.
- Na Windows ma byc wymuszone wsparcie dla `OpenCode` w `VSCode`.
- Glowne srodowisko developerskie to `WSL2`, nie natywny Python na Windows.
- Stare skrypty z `tools/windows/` nalezy oznaczyc jako legacy/archive i przestac promowac je w README.

## Deliverables

- `tools/dev/setup_windows_host.ps1`
- `tools/dev/setup_wsl2_dev.sh`
- `.vscode/extensions.json`
- aktualizacja `.vscode/settings.json`
- aktualizacja `README.md`
- aktualizacja `README-DEV.md`
- aktualizacja `tools/README.md`
- archiwizacja lub zdeprecjonowanie obecnych skryptow z `tools/windows/`

## Zakres skryptu Windows host

Plik: `tools/dev/setup_windows_host.ps1`

### Odpowiedzialnosc

- walidacja srodowiska hosta
- konfiguracja workspace pod `VSCode`
- instalacja rozszerzen `VSCode`
- przygotowanie uzytkownika do otwarcia repo w `Remote - WSL`

### Czego skrypt nie robi

- nie instaluje `WSL2`
- nie instaluje `Git`
- nie instaluje `VSCode`
- nie instaluje globalnego Pythona na Windows
- nie tworzy `.venv` na Windows
- nie uruchamia testow na Windows jako primary flow

### Kroki

1. Sprawdz, czy skrypt zostal uruchomiony z root repo.
2. Sprawdz obecnosc `git`, `wsl` i `code`.
3. Jesli ktoregos narzedzia brakuje, zakoncz z krotka instrukcja recznej instalacji.
4. Utworz lub zaktualizuj pliki repo dla `VSCode`.
5. Zainstaluj rozszerzenia `VSCode` przez `code --install-extension`.
6. Zweryfikuj, czy `OpenCode` dla `VSCode` jest zainstalowany na Windows.
7. Wyswietl koncowa instrukcje:
   - otworz repo w `VSCode`
   - uzyj `Remote - WSL`
   - uruchom `tools/dev/setup_wsl2_dev.sh` w terminalu WSL

### Lista rozszerzen VSCode

- `ms-vscode-remote.remote-wsl`
- `ms-python.python`
- `ms-python.vscode-pylance`
- `charliermarsh.ruff`
- `ms-playwright.playwright`
- `Vue.volar`
- `sst-dev.opencode`

## Zakres skryptu WSL2

Plik: `tools/dev/setup_wsl2_dev.sh`

### Odpowiedzialnosc

- przygotowanie runtime dev/test w WSL2
- pobranie wlasciwego Pythona
- utworzenie `.venv`
- instalacja zaleznosci Python
- instalacja zaleznosci Node dla `framework/visual/ui`
- przygotowanie repo do pracy z `make`, `pytest`, Playwright i UI report

### Narzedzia rekomendowane

- Python: `uv`
- Node 22: `fnm`
- pakiety systemowe: tylko minimalne zaleznosci wymagane przez Python/Playwright/Node

### Kroki

1. Sprawdz, czy skrypt dziala wewnatrz `WSL2`.
2. Sprawdz, czy repo zostalo uruchomione z jego root katalogu.
3. Sprawdz obecnosc podstawowych narzedzi systemowych:
   - `curl`
   - `bash`
   - `git`
4. Zainstaluj `uv`, jesli go brakuje.
5. Pobierz Python `3.13.x` przez `uv`.
6. Utworz `.venv` w root repo.
7. Zainstaluj zaleznosci:
   - `python -m pip install --upgrade pip`
   - `python -m pip install -e ".[dev]"`
8. Zainstaluj Playwright Chromium.
9. Zainstaluj `fnm`, jesli go brakuje.
10. Zainstaluj i aktywuj `Node 22`.
11. W `framework/visual/ui` uruchom `npm ci`.
12. Opcjonalnie zbuduj UI przez `npm run build:fast`, aby `make report-serve` dzialal od razu.
13. Wyswietl koncowe komendy weryfikacyjne.

## Konfiguracja VSCode w repo

### `.vscode/extensions.json`

Plik ma zawierac rekomendacje rozszerzen wymaganych do pracy z repo.

### `.vscode/settings.json`

Plik ma zostac rozszerzony o ustawienia pod workflow WSL2:

- `python.defaultInterpreterPath` wskazujace na `.venv/bin/python`
- `python.testing.pytestEnabled: true`
- `python.testing.unittestEnabled: false`
- `python.testing.pytestArgs: ["qa"]`
- `python.terminal.activateEnvironment: true`

Ustawienia maja pozostac lekkie i workspace-scoped.

## Zmiany w README.md

### Sekcja Quick Start

Nalezy przepisac sekcje tak, aby promowala:

- `Windows + VSCode + WSL2` jako rekomendowany flow
- uruchomienie skryptu hosta Windows
- nastepnie uruchomienie skryptu WSL2

### Nalezy usunac lub zdeprecjonowac

- promowanie obecnego `tools/windows/setup_windows.ps1` jako glownej sciezki
- stary flow oparty o reczny `pyenv` jako glowny onboarding
- instrukcje sugerujace natywny dev Python na Windows

### Nalezy dodac

- krotka sekcje `VSCode`
- krotka sekcje `OpenCode`
- informacje, ze runtime dev jest w `WSL2`
- informacje, ze UI lives in `framework/visual/ui` i wymaga `Node 22`

## Zmiany w README-DEV.md

Nalezy dodac sekcje `Development Environment` z:

- oficjalnym modelem pracy `Windows host + WSL2`
- opisem obu skryptow bootstrap
- informacja, ze `make check` nie obejmuje UI
- informacja, ze dla `framework/visual/ui` trzeba uzywac:
  - `npm ci`
  - `npm run test:unit`
  - `npm run build:fast`

Nalezy doprecyzowac, ze:

- Python runtime target to `3.13`
- jedyny osobny projekt Node to `framework/visual/ui`
- `VSCode` jest domyslnym IDE dla tego repo

## Zmiany w tools/README.md

Nalezy:

- dodac sekcje `tools/dev/`
- opisac nowe skrypty bootstrap
- usunac lub poprawic martwe odniesienie do `tools/opencode/README.md`
- oznaczyc `tools/windows/` jako legacy/archive, jesli zostana przeniesione

## Los obecnych skryptow tools/windows

Rekomendacja:

- nie usuwac od razu
- przeniesc do `tools/windows/archive/` albo oznaczyc jako `legacy`
- usunac ich promocje z `README.md`
- dodac krotki komentarz, ze nie sa juz oficjalnym onboardingiem

## Weryfikacja po wdrozeniu

### Host Windows

- `code --list-extensions`
- potwierdzenie obecnosci `sst-dev.opencode`
- potwierdzenie obecnosci `ms-vscode-remote.remote-wsl`

### WSL2

- `.venv/bin/python --version`
- `make help`
- `make test-aso`
- `python -m pytest --collect-only -q`

### UI

W katalogu `framework/visual/ui`:

- `npm ci`
- `npm run test:unit`
- `npm run build:fast`

## Kolejnosc implementacji

1. Dodac nowe skrypty do `tools/dev/`.
2. Dodac `.vscode/extensions.json`.
3. Zaktualizowac `.vscode/settings.json`.
4. Zaktualizowac `README.md`.
5. Zaktualizowac `README-DEV.md`.
6. Zaktualizowac `tools/README.md`.
7. Oznaczyc stare `tools/windows/` jako legacy/archive.
8. Zweryfikowac bootstrap na czystym Windows host i swiezym WSL2.

## Ryzyka

- instalacja rozszerzen `VSCode` przez `code` moze wymagac dzialajacego CLI `code` w PATH
- automatyczna instalacja Node 22 w WSL2 wymaga stabilnego i przewidywalnego mechanizmu
- Playwright na Linux moze wymagac dodatkowych pakietow systemowych
- czesc uzytkownikow moze nadal probowac pracowac natywnie na Windows, wiec README musi to jasno odradzac

## Rekomendacje techniczne

- Python bootstrap oprzec o `uv`, nie o reczne instalatory
- runtime dev dokumentowac tylko dla `WSL2`
- `VSCode` konfigurowac glownie przez repo files plus instalacje rozszerzen
- nie dotykac globalnego `git config`
- nie robic interaktywnych wizardow, tylko przewidywalne skrypty z czytelnym logiem
