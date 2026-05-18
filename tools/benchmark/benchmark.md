# Benchmark E2E - instrukcja dla AI

## Cel

Benchmark porównawczy wydajności testów E2E w różnych trybach uruchamiania:
- **headless sekwencyjnie** (baseline)
- **headless xdist -n 2/3/4** (2, 3, 4 workery)

Każdy tryb uruchamiany jest 2 razy. Łącznie 4 tryby x 2 runy = 8 przebiegów.

---

## Prompt do wklejenia dla AI

Poniższy prompt można wkleić do OpenCode / Copilot / innego agenta, aby odtworzyć benchmark:

```
Uruchom benchmark wydajności testów E2E z pliku:
qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py

Parametry:
- 2x headless sekwencyjnie (HEADLESS=1, bez xdist)
- 2x headless xdist -n 2
- 2x headless xdist -n 3
- 2x headless xdist -n 4

Dla każdego runu:
- env: REPORTING_ENABLED=0 ALLURE_ENABLED=0 PYTEST_HTML_ENABLED=0 RECORD_VIDEO=0
- HEADLESS=1
- komenda bazowa: .venv/bin/python -m pytest <plik> -v --tb=line
- dla xdist dodaj: -n <N>
- zapisz: czas trwania (wall + pytest), liczbę passed/failed, listę FAILED testów, exit code

Użyj skryptu tools/benchmark/run_benchmark.sh do uruchomienia.
Wyniki surowe: bench_raw_<timestamp>.txt
Zestawienie: bench_summary_<timestamp>.md

Format wyników:
1. Tabela podsumowująca (tryb | run 1 | run 2 | avg czas | min | max | avg passed | pass rate)
2. Tabele szczegółowe per tryb (run | czas | passed | failed | exit code | failures)
3. Porównanie speedup xdist vs sekwencyjny (headless)
4. Flakey analysis - najczęściej padające testy
```

---

## Skrypt

Gotowy skrypt: [`run_benchmark.sh`](run_benchmark.sh)

Uruchomienie:

```bash
bash tools/benchmark/run_benchmark.sh
```

Wyniki surowe trafiają do `bench_raw_<timestamp>.txt`, zestawienie markdown do `bench_summary_<timestamp>.md` -- oba w katalogu głównym repozytorium.

---

## Interpretacja wyników

### Speedup xdist

```
speedup = avg_czas_sekwencyjny / avg_czas_xdist_N
```

Idealny speedup dla N workerów = N. W praktyce overhead xdist + współdzielony serwer testowy
obniżają go. Typowe wartości:

| Workery | Idealny speedup | Realistyczny zakres |
|---------|----------------|---------------------|
| 2       | 2.0x           | 1.4x - 1.8x        |
| 3       | 3.0x           | 1.8x - 2.5x        |
| 4       | 4.0x           | 2.0x - 3.0x         |

### Flakey testy

Test jest flakey jeśli pada w >1 runie z łącznej puli, niezależnie od trybu. Sprawdź:
- Czy pada częściej w xdist (problem z współbieżnością / sesją)?
- Czy pada częściej sekwencyjnie (problem z timeoutem / stanem)?
- Jaki błąd dominuje (timeout vs element not found vs RuntimeError)?

---

## Uwagi

- Benchmark obciąża serwer testowy. Obecna konfiguracja to 8 runów (4 tryby x 2 przebiegi).
- Runy xdist -n 4 mogą powodować większy flake rate przez obciążenie serwera.
- Jeśli runy pod koniec sesji masowo padają, to zazwyczaj degradacja serwera, nie problem z testami.
