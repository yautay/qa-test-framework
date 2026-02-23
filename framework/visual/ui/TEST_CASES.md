# Przypadki testowe dla logiki wysyłania raportów

## Scenariusze

### A) Zewnętrzny API działa (odpowiada 200)

| # | Stan przed | Akcja | Oczekiwany wynik | Test Frontend | Test Server |
|---|-----------|-------|------------------|---------------|------------|
| A1 | Nowy BUG (bug=true, bug_reported=false) | Kliknij REPORT | → prompt | ✅ | - |
| A2 | Nowa ASO (aso=true, asoreported=false) | Kliknij REPORT | → prompt | ✅ | - |
| A5 | BUG już wysłany (bug=true, bug_reported=true) | Kliknij REPORT | → PDF bez promptu | ✅ | - |
| A6 | ASO już wysłana | Kliknij REPORT | → PDF bez promptu | ✅ | - |
| A8 | Wszystko wysłane + brak BUG | Kliknij REPORT | → nic (disabled) | ✅ | - |

### B) Zewnętrzny API nie działa (timeout/błąd)

| # | Stan przed | Akcja | Oczekiwany wynik | Test |
|---|-----------|-------|------------------|------|
| B1 | Nowy BUG → wysyłka FAIL | Kliknij REPORT (1x) | → prompt → retry cichy | ✅ |
| B2 | Nowy BUG → wysyłka FAIL | Kliknij REPORT ponownie | → cichy retry (brak nowych) | ✅ |
| B3 | Po FAIL + nowy kandydat | Kliknij REPORT | → prompt | ✅ |
| B4 | Brak kandydatów + są BUG | Kliknij REPORT | → PDF bez promptu | ✅ |
| B5 | Brak kandydatów + brak BUG | Kliknij REPORT | → nic | ✅ |

### C) Retry po błędzie

| # | Stan przed | Akcja | Oczekiwany wynik | Test |
|---|-----------|-------|------------------|------|
| C1 | Poprzednia próba failed + brak nowych kandydatów | Kliknij REPORT | → cichy retry | ✅ |
| C2 | Poprzednia próba failed + nowi kandydaci | Kliknij REPORT | → prompt | ✅ |

---

## Testy serwera

### Testy dla funkcji `_read_last_audit_entry`

| Test | Opis |
|------|------|
| `test_returns_none_when_no_audit_file` | Brak pliku = None |
| `test_returns_none_when_file_empty` | Pusty plik = None |
| `test_returns_none_when_file_invalid_json` | Invalid JSON = None |
| `test_returns_last_entry_from_list` | Zwraca ostatni wpis z listy |
| `test_returns_none_when_list_empty` | Pusta lista = None |

### Testy dla funkcji `_had_previous_failures`

| Test | Opis |
|------|------|
| `test_returns_false_when_none` | Brak auditu = False |
| `test_returns_false_when_no_failures` | Wszystko OK = False |
| `test_returns_true_when_bug_failed` | BUG failed = True |
| `test_returns_true_when_aso_failed` | ASO failed = True |
| `test_returns_false_when_missing_keys` | Brak kluczy = False |
| `test_returns_false_when_empty_dict` | Pusty dict = False |

---

## Implementacja testów

### Testy getterów (`src/stores/resultsStore.test.js`)

Testy jednostkowe dla:
- `reportCandidatesCount` - liczenie kandydatów do wysłania
- `hasAnyBug` - sprawdzanie czy są jakiekolwiek BUG

### Testy logiki (`src/pages/ReportPage.test.js`)

Testy dla scenariuszy:
- API działa - nowi kandydaci
- API działa - brak nowych kandydatów
- API nie działa - logika retry

### Testy serwera (`qa/aso/framework/visual/test_report_server_units.py`)

Testy dla funkcji:
- `_read_last_audit_entry` - 5 testów
- `_had_previous_failures` - 7 testów

---

## Uruchomienie testów

```bash
# Testy frontendu
cd /mnt/repos/visual-regresion/framework/visual/ui
npm run test:unit

# Testy serwera
cd /mnt/repos/visual-regresion
python -m pytest qa/aso/framework/visual/test_report_server_units.py -v
```
