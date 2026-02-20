# Visual Report UI - Dokumentacja Biznesowa

## 1. Przegląd Aplikacji

Visual Report UI to aplikacja do przeglądania i zarządzania wynikami testów wizualnych (visual regression tests). Umożliwia testerom przeglądanie zrzutów ekranu, tagowanie wyników (BUG, ASO, BASELINE), dodawanie notatek oraz generowanie raportów PDF.

### Główne przypadki użycia

1. **Przegląd wyników testów** - tester widzi listę testów z wynikami (passed/failed/uncertain)
2. **Porównywanie obrazów** - otwiera modal z obrazkami (ref, test, diff, heatmap)
3. **Tagowanie wyników** - oznaczanie testów jako BUG, ASO (acceptable software offset), lub BASELINE
4. **Dodawanie notatek** - dodawanie opisu do konkretnego wyniku testu
5. **Wysyłanie raportu** - wysyłanie oznaczonych wyników do zewnętrznego systemu (Jira/AHA) + generowanie PDF
6. **Zarządzanie baseline** - synchronizacja obrazów referencyjnych

---

## 2. Struktura Danych

### 2.1 Wynik testu (row)

```javascript
{
  scenario_id: string,    // ID scenariusza testowego
  suite_id: string,       // ID zestawu testów
  status: string,         // 'passed' | 'failed' | 'skipped' | 'uncertain'
  actual_path: string,   // ścieżka do obrazka testowego
  baseline_path: string,  // ścieżka do obrazka referencyjnego
  diff_path: string,      // ścieżka do obrazka różnicy
  heatmap_path: string,  // ścieżka do mapy ciepła (LPIPS)
  viewport: string,      // rozmiar ekranu (np. "1920x1080")
  browser: string,        // przeglądarka (np. "chromium")
  message: string,       // opis błędu
  test_metadata: object   // dodatkowe metadane
}
```

### 2.2 Tagi (tagLog)

Klucz tagu tworzony jest z 4 pól: `scenario_id::actual_path::baseline_path::diff_path`

```javascript
{
  "s1::a.png::::": {
    bug: boolean,           // czy oznaczony jako BUG
    bug_reported: boolean,  // czy już wysłany do systemu zewnętrznego
    bug_reported_at: string, // timestamp wysłania
    
   aso: boolean,            // czy oznaczony jako ASO
   aso_reported: boolean,
   aso_reported_at: string,
    
    baseline: boolean,      // czy oznaczony do synchronizacji baseline
    
    note: {                 // obiekt notatki
      text: string,
      updatedAt: string     // timestamp ostatniej edycji
    } | null,
    note_reported: boolean,
    note_reported_at: string,
    note_reported_hash: string  // hash treści już wysłanej
  }
}
```

### 2.3 Lockowanie tagów

Po wysłaniu raportu, tagi są "lockowane" - użytkownik nie może ich usunąć ani zmienić, dopóki nie doda nowej notatki (wtedy unlock dla notatki).

---

## 3. Przepływy (Flows)

### 3.1 Przeglądanie wyników

```
HeroPage (lista raportów)
    ↓ [kliknięcie w raport]
ReportPage (szczegóły raportu)
    ↓ [kliknięcie w wiersz]
ViewerModal (porównanie obrazów)
```

- **HeroPage** (`/`) - lista dostępnych raportów z filtrami
- **ReportPage** (`/:runId`) - szczegóły wybranego raportu z tabelą wyników
- **ViewerModal** - modal z obrazkami: ref, test, diff, heatmap (do 4 slotów)

### 3.2 Tagowanie wyników

```
W ViewerModal:
- Klawisz 'S' → prompt "Dodać BUG?"
- Klawisz 'C' → prompt "Dodać ASO?"
- Klawisz '\' → prompt "Dodać BASELINE?"
- Klawisz 'N' → otwórz edytor notatek
```

Po potwierdzeniu tag jest zapisywany w `tagLog` i synchronizowany z plikiem na dysku (z opóźnieniem 250ms - debounce).

### 3.3 Wysyłanie raportu (kluczowy flow)

```
Użytkownik klika "Wyślij raport" w ReportHeader
    ↓
promptSendReport() sprawdza:
    ├── Czy są elementy do wysłania? (BUG/ASO/NOTES)
    ├── Czy były poprzednie nieudane próby?
    ├── Czy są jakiekolwiek BUG (nawet już wysłane)?
    ↓
Decyzja:
    ├── NIE ma kandydatów, ale BYŁY błędy → silent retry (bez pytania)
    ├── NIE ma kandydatów, ale są BUGi → generuj PDF bez pytania
    ├── NIE ma nic do wysłania → informacja "Nothing to send"
    ├── Są kandydaci → pytaj o potwierdzenie
    ↓
executeSendReport() → API POST /api/reports/{id}/report/send
    ├── payload: { tag_snapshot: {...} }
    ├── response: { bug: {...},aso: {...},note: {...},pdf: {...}, tag_snapshot: {...} }
    ├── Jeśli PDF wygenerowany → automatyczne pobranie
    └── Aktualizacja tagLog z odpowiedzi (lockowanie)
```

#### Szczegóły logiki decyzyjnej

| Kandydaci do wysłania | Poprzednie błędy | Jakieś BUGi | Akcja |
|-----------------------|------------------|-------------|-------|
| ❌ | ✅ | ❌ | Silent retry |
| ❌ | ❌ | ✅ | Generuj PDF (cicho) |
| ❌ | ❌ | ❌ | Nic nie rób |
| ✅ | - | - | Pytaj o potwierdzenie |

**Kandydat do wysłania** = BUG nie wysłany LUB ASO nie wysłane LUB nowa/notatka nie wysłana LUB notatka edytowana po ostatnim wysłaniu

### 3.4 Synchronizacja baseline

```
Użytkownik klika "Wyślij baseline"
    ↓
Pobierz challenge ( CAPTCHA ) z serwera
    ↓
Użytkownik musi przepisać frazę (ochrona przed przypadkowym nadpisaniem)
    ↓
Wyślij wybrane obrazy do API
```

---

## 4. Architektura Komponentów

### 4.1 Strony (pages/)

| Komponent | Ścieżka | Opis |
|-----------|---------|------|
| `HeroPage.vue` | `/` | Lista raportów, filtry, auto-refresh |
| `ReportPage.vue` | `/:runId` | Tabela wyników, filtry, akcje |

### 4.2 Komponenty (components/)

| Komponent | Opis |
|----------|------|
| `AppHeader.vue` | Nagłówek aplikacji (logo, język) |
| `ReportHeader.vue` | Nagłówek raportu (ID, przyciski akcji) |
| `FiltersPanel.vue` | Filtry wyników (status, viewport, browser, tekst) |
| `ResultsTable.vue` | Tabela z wynikami testów |
| `ViewerModal.vue` | Modal do przeglądania obrazów |
| `ConfirmPrompt.vue` | Modal potwierdzenia (tak/nie) |
| `TestMetadataPanel.vue` | Panel metadanych testu |

### 4.3 Komponenty Hero (components/hero/)

| Komponent | Opis |
|----------|------|
| `HeroHeader.vue` | Nagłówek strony głównej |
| `ReportsFilters.vue` | Filtry na liście raportów |
| `ReportsList.vue` | Lista raportów |
| `ReportCard.vue` | Karta pojedynczego raportu |
| `ReportsEmptyState.vue` | Stan pustej listy |

### 4.4 Store (Pinia)

| Store | Odpowiedzialność |
|-------|-----------------|
| `resultsStore.js` | Wyniki testów, filtry, tagi, stan modala |
| `reportsStore.js` | Lista raportów, auto-refresh |

### 4.5 Biblioteki (lib/)

| Moduł | Opis |
|-------|------|
| `viewer.js` | Logika parsowania ścieżek, klucze tagów |
| `api/reportsApi.js` | API do komunikacji z backendem |
| `baselineApi.js` | API do synchronizacji baseline |
| `notes.js` | Walidacja i sanityzacja notatek |
| `tagPersistence.js` | Zapis/odczyt tagów do pliku |
| `format.js` | Formatowanie wyświetlanych danych |
| `i18n/` | Wielojęzyczność (en, pl, uk) |

---

## 5. API Backend

### 5.1 Endpointy

| Metoda | Ścieżka | Opis |
|--------|---------|------|
| `GET` | `/api/reports` | Lista raportów |
| `GET` | `/api/reports/{id}/results` | Wyniki testów dla raportu |
| `GET` | `/api/reports/{id}/image/ref` | Obraz referencyjny (dynamiczny) |
| `POST` | `/api/reports/{id}/report/send` | Wysłanie raportu |
| `GET` | `/api/baseline/challenge` | Challenge dla baseline |
| `POST` | `/api/baseline/submit` | Wysłanie baseline |

### 5.2 Format odpowiedzi sendReport

```javascript
{
  bug: {
    sent: number,      // ile wysłano pomyślnie
    failed: number,    // ile nie wysłano (błąd API)
    skipped_locked: number  // ile pominięto (locked)
  },
  aso: { ... },
  note: { ... },
  pdf: {
    pages: number      // ile stron wygenerowano
  },
  previous_attempt_had_failures: boolean,  // czy poprzednia próba miała błędy
  tag_snapshot: { ... }   // zaktualizowany stan tagów
}
```

---

## 6. Mechanizmy Specjalne

### 6.1 Debounce zapisu tagów

Zmiany tagów nie są zapisywane od razu do pliku. Używany jest `setTimeout(250ms)` - jeśli użytkownik szybko zmienia tagi, zapis następuje dopiero po 250ms bezczynności.

### 6.2 Lockowanie tagów

Po wysłaniu raportu, tagi które zostały wysłane są lockowane:
- `tagLocked[key].bug = true` - jeśli bug wysłany
- `tagLocked[key].aso = true` - jeśli ASO wysłane

Lockuniętego taga nie można usunąć klawiszem. Odblokowanie następuje gdy:
- Dla notatek: użytkownik doda nową treść (nowy timestamp > poprzedni reported_at)

### 6.3 Hash treści notatki

Przy wysyłaniu notatki, obliczany jest hash treści i zapisywany jako `note_reported_hash`. Przy ponownej próbie wysłania, jeśli hash się nie zmienił, notatka jest pomijana (nie wysyłana ponownie).

### 6.4 Super Zoom

Przy wciśnięciu klawisza 'W' (lub trzymaniu myszy na obrazku) aktywuje się tryb super zoom - obraz powiększa się 3x (100% + 200%) z transformacją origin na pozycję kursora.

### 6.5 Klawisze skrótów

| Klawisz | Kontekst | Akcja |
|---------|----------|-------|
| `1-4` | Modal | Liczba kolumn (slotów) |
| `A` | Modal | Poprzedni obraz |
| `D` | Modal | Następny obraz |
| `W` | Modal | Super zoom (trzymaj) |
| `S` | Modal | Dodaj BUG |
| `C` | Modal | Dodaj ASO |
| `\` | Modal | Dodaj BASELINE |
| `N` | Modal | Otwórz edytor notatek |
| `Space` | Modal/Tabela | Otwórz modal / Potwierdź prompt |
| `Shift` | Modal/Tabela | Zamknij modal / Anuluj prompt |
| `Esc` | Modal | Zamknij modal |
| `↑/↓` | Tabela | Nawigacja po wierszach |

---

## 7. Testy

Testy jednostkowe znajdują się w tych samych katalogach co pliki źródłowe, z rozszerzeniem `.test.js`.

```bash
# Uruchomienie testów
npm run test:unit        # tylko testy
npm run test:coverage    # z pokryciem kodu
npm run build            # build + testy + coverage
```

### 7.1 Pokrycie testami

- `resultsStore.test.js` - testy getterów (`reportCandidatesCount`, `hasAnyBug`)
- `ReportPage.test.js` - testy funkcji promptowania
- `reportsStore.test.js` - testy pobierania listy raportów
- `viewer.test.js` - testy parsowania ścieżek
- `notes.test.js` - testy walidacji notatek
- Testy serwera w `qa/aso/framework/visual/test_report_server_units.py`

---

## 8. Zależności

### 8.1 Frontend

- **Vue 3** - framework UI
- **Pinia** - state management
- **Bootstrap 5** - komponenty UI
- **Vite** - bundler
- **Vitest** - testy jednostkowe

### 8.2 Backend (report_server.py)

- **Flask/Python** - serwer HTTP
- Raportowanie do zewnętrznych systemów (AHA/Jira)
- Generowanie PDF z konfiguracji `bug_report_pdf_config.json`

---

## 9. Pliki Konfiguracyjne

| Plik | Opis |
|------|------|
| `bug_report_pdf_config.json` | Szablon PDF (nagłówek, stopka, logo) |
| `vitest.config.js` | Konfiguracja testów |
| `vite.config.js` | Konfiguracja bundlera |
| `package.json` | Zależności npm |
| `i18n/locales/{en,pl,uk}.json` | Tłumaczenia |

---

## 10. Typowe problemy i rozwiązania

### 10.1 Prompt pokazuje się w pętli

**Przyczyna:** Flaga `isSendingInProgress` nie jest ustawiona podczas wysyłania.

**Rozwiązanie:** Sprawdź czy `executeSendReport` ustawia `isSendingInProgress = true` na początku i `false` w bloku `finally`.

### 10.2 PDF nie generuje się mimo BUG

**Przyczyna:** Logika decyzyjna w `promptSendReport` nie uwzględnia poprawnie stanu `hasAnyBug`.

**Rozwiązanie:** Upewnij się, że getter `hasAnyBug` w `resultsStore.js` poprawnie zlicza tagi z `bug: true`.

### 10.3 Po błędzie API nie pyta ponownie

**Przyczyna:** Serwer nie zwraca pola `previous_attempt_had_failures`.

**Rozwiązanie:** Sprawdź czy `report_server.py` zwraca to pole w odpowiedzi `/report/send`.

### 10.4 Testy klucza tagu nie przechodzą

**Przyczyna:** Klucz musi mieć dokładnie 4 pola oddzielone `::`, nawet jeśli pola są puste.

**Rozwiązanie:** Używaj formatu `scenario_id::actual_path::baseline_path::diff_path`, np. `"s1::a.png::::"`.
