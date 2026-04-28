# Benchmark E2E - instrukcja dla AI

## Cel

Benchmark porównawczy wydajności testów E2E w różnych trybach uruchamiania:
- **headless sekwencyjnie** (baseline)
- **headless xdist -n 2** (2 workery)
- **headless xdist -n 3** (3 workery)
- **headless xdist -n 4** (4 workery)

Każdy tryb uruchamiany jest 5 razy, aby uzyskać statystycznie użyteczne wyniki.

---

## Prompt do wklejenia dla AI

Poniższy prompt można wkleić do OpenCode / Copilot / innego agenta, aby odtworzyć benchmark:

```
Uruchom benchmark wydajności testów E2E z pliku:
qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py

Parametry:
- 5x headless sekwencyjnie (HEADLESS=1, bez xdist)
- 5x headless xdist -n 2
- 5x headless xdist -n 3
- 5x headless xdist -n 4

Dla każdego runu:
- env: HEADLESS=1 REPORTING_ENABLED=0 ALLURE_ENABLED=0 PYTEST_HTML_ENABLED=0 RECORD_VIDEO=0
- komenda bazowa: .venv/bin/python -m pytest <plik> -v --tb=line
- dla xdist dodaj: -n <N>
- zapisz: czas trwania (wall + pytest), liczbę passed/failed, listę FAILED testów, exit code

Użyj skryptu tools/benchmark/run_benchmark.sh do uruchomienia.
Wyniki zapisz do pliku bench_<data>.md w katalogu głównym repozytorium.

Format wyników:
1. Tabela podsumowująca (tryb | avg czas | min | max | avg passed | pass rate)
2. Tabele szczegółowe per tryb (run | czas pytest | passed | failed | failures)
3. Porównanie speedup xdist vs sekwencyjny (czas xdist / czas seq)
4. Najczęściej padające testy (flakey analysis)
5. Najczęstsze błędy
```

---

## Skrypt

Gotowy skrypt: [`run_benchmark.sh`](run_benchmark.sh)

Uruchomienie:

```bash
bash tools/benchmark/run_benchmark.sh
```

Wyniki surowe trafiają do `bench_raw_<timestamp>.txt` w katalogu głównym repozytorium.

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

Test jest flakey jeśli pada w >1 runie z 5, niezależnie od trybu. Sprawdź:
- Czy pada częściej w xdist (problem z współbieżnością / sesją)?
- Czy pada częściej sekwencyjnie (problem z timeoutem / stanem)?
- Jaki błąd dominuje (timeout vs element not found vs RuntimeError)?

---

## Uwagi

- Benchmark obciąża serwer testowy przez ~2-3 godziny. Nie uruchamiaj równolegle z innymi testami.
- Runy xdist -n 4 mogą powodować większy flake rate przez obciążenie serwera.
- Jeśli runy pod koniec sesji masowo padają, to zazwyczaj degradacja serwera, nie problem z testami.
- Timeout skryptu: 5h (18000s). Przy 20 runach po ~20 min = ~6.5h max, więc xdist powinien skrócić total.
