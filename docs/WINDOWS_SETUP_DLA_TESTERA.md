# Windows Setup Dla Testera

Ta instrukcja jest dla osoby, ktora chce uruchamiac testy i report lokalnie na Windows, ale nie musi znac technicznych detali frameworka.

## Co bedzie potrzebne

1. Komputer z Windows 10 lub Windows 11.
2. Dostep do internetu.
3. Folder z tym repozytorium na dysku.
4. Git for Windows.
5. Opcjonalnie Docker Desktop.

Docker Desktop jest potrzebny tylko do dodatkowych uslug, np. lokalnego MinIO albo remote grid.
Do zwyklego uruchamiania testow i reportu nie jest wymagany.

Node.js nie jest potrzebny testerowi.

## Zanim zaczniesz

1. Upewnij sie, ze masz juz skopiowany folder projektu na dysku.
2. Upewnij sie, ze folder projektu nie jest otwarty z pendrive albo dysku sieciowego o slabym polaczeniu.
3. Zamknij stare okna terminala, jesli byly wczesniej otwierane dla tego projektu.

## Pierwsza instalacja krok po kroku

1. Otworz folder projektu w Eksploratorze Windows.
2. Wejdz do folderu `tools\windows`.
3. Kliknij dwa razy `Setup_Windows.cmd`.
4. Poczekaj, az instalacja sie zakonczy.

W trakcie instalacji skrypt zrobi za Ciebie:

1. sprawdzenie i instalacje `uv`,
2. przygotowanie Pythona `3.13.2`,
3. utworzenie lokalnego srodowiska `.venv`,
4. instalacje wszystkich wymaganych bibliotek,
5. instalacje przegladarki Chromium dla Playwright,
6. podpiecie lokalnego hooka git.

Pierwsze uruchomienie moze potrwac kilka minut.

## Sprawdzenie czy wszystko dziala

Po zakonczeniu instalacji:

1. Kliknij prawym przyciskiem myszy w folder projektu.
2. Otworz PowerShell w tym folderze.
3. Wklej i uruchom:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 doctor
```

Jesli wszystko jest poprawnie przygotowane, zobaczysz komunikaty `OK` i na koncu informację, ze nie ma blokujacych problemow.

## Codzienna praca

Zawsze pracuj z katalogu glownego repozytorium.

Najprosciej:

1. Otworz PowerShell w folderze projektu.
2. Wklej jedna z gotowych komend.

### Uruchomienie testow ASO

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 aso
```

### Uruchomienie testow API

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 api
```

### Uruchomienie testow E2E

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 e2e
```

### Uruchomienie testow visual

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual
```

### Sprawdzenie konfiguracji frameworka

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 verify
```

## Jak uruchomic report

1. Otworz PowerShell w folderze projektu.
2. Wklej i uruchom:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 report
```

3. Poczekaj, az w terminalu pojawi sie adres serwera.
4. Otworz przegladarke i wejdz na podany adres.

Najczesciej bedzie to:

```text
http://127.0.0.1:4173/
```

Wazne:

1. Report działa bez Node.js po stronie testera.
2. Jesli repo jest aktualne, nie trzeba nic dodatkowo budowac.

## Po aktualizacji repozytorium

Jesli zrobisz `git pull`, najlepiej odswiezyc srodowisko jedna z dwoch metod.

Szybka metoda:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 sync
```

Pelna metoda, gdy cos zachowuje sie dziwnie:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

## Kiedy potrzebny jest Docker Desktop

Docker Desktop jest opcjonalny.

Przyda sie tylko wtedy, gdy potrzebujesz:

1. lokalnego MinIO do visual baseline,
2. lokalnego remote grid.

Przyklady:

```powershell
docker compose -f tools\minio\docker-compose.yml up -d
docker compose -f tools\minio\docker-compose.yml down

docker compose -f tools\remote\docker-compose.yml up -d
docker compose -f tools\remote\docker-compose.yml down
```

## Najczestsze problemy

### 1. Skrypt nie startuje po dwukliku

Uruchom go z PowerShella:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

### 2. `doctor` pokazuje blad przy `.venv` albo `python`

Uruchom ponownie bootstrap:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

### 3. `doctor` pokazuje ostrzezenie dla Docker

To nie blokuje zwyklej pracy testera.
Mozesz to zignorowac, jesli nie uzywasz MinIO ani remote grid.

### 4. Chromium / Playwright nie dziala

Uruchom ponownie bootstrap. Skrypt jeszcze raz sprawdzi i doinstaluje potrzebne elementy.

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

### 5. Report nie otwiera sie w przegladarce

1. Sprawdz, czy komenda `report` nadal dziala w terminalu.
2. Sprawdz, czy otwierasz adres pokazany przez terminal.
3. Jesli nadal nie dziala, wykonaj `git pull`, potem `sync`, a na koncu uruchom report jeszcze raz.

### 6. Czy `Setup_Windows.cmd` poprosi o uprawnienia administratora?

Zwykle nie.

Ten setup jest przygotowany tak, aby instalowal rzeczy lokalnie dla aktualnego uzytkownika.
Dotyczy to w szczegolnosci:

1. `uv`
2. Python `3.13.2`
3. `.venv`
4. bibliotek Python
5. Playwright Chromium

Wyjatki, kiedy moze pojawic sie prompt albo blokada:

1. firmowa polityka Windows blokuje `winget` lub uruchamianie skryptow,
2. Git for Windows nie jest jeszcze zainstalowany i Wasza organizacja wymaga admina do jego instalacji,
3. komputer ma dodatkowe zabezpieczenia narzucone przez IT.

Najkrotsza odpowiedz:

1. sam `Setup_Windows.cmd` zwykle nie wymaga admina,
2. ale polityki firmowe moga to zmienic.

## Najkrotsza wersja dla testera

Pierwszy raz:

1. `tools\windows\Setup_Windows.cmd`
2. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 doctor`

Na co dzien:

1. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 aso`
2. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 e2e`
3. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual`
4. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 report`

Po `git pull`:

1. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 sync`

## Co musi byc zainstalowane w Windows przed startem

Ponizej jest praktyczna lista dla testera.

### Rzeczy wymagane

1. Git for Windows
2. Dostep do internetu
3. Repozytorium sklonowane na dysk albo przekazane jako gotowy folder

### Rzeczy instalowane automatycznie przez bootstrap

1. `uv`
2. Python `3.13.2`
3. lokalne srodowisko `.venv`
4. biblioteki Python z `uv.lock`
5. Playwright Chromium
6. lokalny hook git

### Rzeczy opcjonalne

1. Docker Desktop, tylko jesli chcesz uzywac MinIO albo remote grid
2. Node.js `22`, tylko dla osoby rozwijajacej aplikacje report UI

## Lista oprogramowania i czy wymaga administratora

| Element | Czy potrzebny testerowi | Kto to instaluje | Czy zwykle wymaga admina | Uwagi |
| --- | --- | --- | --- | --- |
| Git for Windows | Tak | tester lub IT | Zwykle nie, jesli instalacja jest per-user; czasem tak w srodowisku firmowym | Potrzebny do pracy z repo i hooka git |
| `uv` | Tak | bootstrap | Zwykle nie | Bootstrap probuje zainstalowac go sam |
| Python `3.13.2` | Tak | bootstrap przez `uv` | Nie | Instalowany lokalnie dla uzytkownika |
| Biblioteki Python z `uv.lock` | Tak | bootstrap | Nie | Instaluja sie do lokalnego `.venv` |
| Playwright Chromium | Tak | bootstrap | Nie | Instalowany lokalnie w profilu uzytkownika |
| Report UI `dist` | Tak | jest juz w repo | Nie | Tester nic nie buduje lokalnie |
| Docker Desktop | Opcjonalnie | tester lub IT | Tak, zazwyczaj tak | Potrzebny tylko do MinIO / remote grid |
| Node.js `22` | Nie dla testera | maintainer UI lub IT | Zwykle nie | Potrzebny tylko do zmian w `framework/visual/ui` |

## Najkrotsza odpowiedz: co trzeba miec przed startem

Dla zwyklego testera najczesciej wystarczy:

1. Windows
2. Git for Windows
3. folder repozytorium
4. internet

Reszte przygotuje `Setup_Windows.cmd`.

Jesli potrzebujesz Docker Desktop, to jego instalacja najczesciej wymaga uprawnien administratora.
