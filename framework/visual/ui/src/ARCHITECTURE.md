# Visual Report UI - Dokumentacja Biznesowa

## 1. Przeglad Aplikacji

Visual Report UI to aplikacja do przegladania wynikow testow wizualnych. Umozliwia:
- przegladanie listy buildow (Hero page)
- podglad szczegolow builda i testow (Raport)
- podglad pojedynczego test case w modalu

Brak logowania uzytkownikow. Stan trwaly znajduje sie po stronie serwera w katalogu artefaktow i jest jedynym zrodlem prawdy.

---

## 2. Struktura Danych

### 2.1 Wynik testu (row)

```javascript
{
  scenario_id: string,
  suite_id: string,
  status: string,
  actual_path: string,
  baseline_path: string,
  diff_path: string,
  heatmap_path: string,
  viewport: string,
  browser: string,
  message: string,
  test_metadata: object
}
```

### 2.2 state.json (per build)

Plik: `artifacts/<run_id>/state.json`

```json
{
  "test_cases": {
    "<case_id>": {
      "bug": { "locked": false, "synced": false, "note": "" },
      "aso": { "locked": false, "synced": false, "note": "" }
    }
  },
  "outbox": [
    {
      "event_id": "uuid",
      "type": "BUG_SET | ASO_SET",
      "payload": { "note": "optional <=500" },
      "status": "pending | sent | failed",
      "attempts": 0,
      "last_attempt_at": "",
      "sent_at": "",
      "last_error": "",
      "test_case_id": "<case_id>"
    }
  ]
}
```

`case_id` to klucz zbudowany z: `scenario_id::actual_path::baseline_path::diff_path`.

### 2.3 build.lock.json

Plik: `artifacts/<run_id>/build.lock.json`

```json
{
  "build_id": "<run_id>",
  "lock_id": "uuid",
  "owner_client_id": "uuid",
  "created_at": 1700000000,
  "last_heartbeat_at": 1700000010,
  "expires_at": 1700000120
}
```

Lock zakladany jest przy wejsciu do Raportu lub otwarciu Modala i odnawiany heartbeatem.

---

## 3. Przeplywy (Flows)

### 3.1 Przegladanie wynikow

```
HeroPage (lista buildow)
    ↓
ReportPage (szczegoly builda)
    ↓
ViewerModal (szczegoly test case)
```

HeroPage nie wymaga locka.

### 3.2 Lock i heartbeat

- Frontend generuje `client_id` i zapisuje w `localStorage` pod kluczem `app.client_id`.
- Przy wejsciu do Raportu lub otwarciu Modala: `POST /api/builds/{id}/lock/acquire`.
- Heartbeat co ~15s: `POST /api/builds/{id}/lock/heartbeat`.
- Lock TTL: 90-120s.
- Release best-effort przy wyjsciu: `POST /api/builds/{id}/lock/release`.

### 3.3 BUG/ASO

```
Uzytkownik w ViewerModal:
  - klawisz 'S' lub 'C' albo klik w UI
  - prompt potwierdzenia + opcjonalna notatka (<=500)
  ↓
POST /api/builds/{id}/events (BUG_SET / ASO_SET)
  - backend zapisuje domenowy stan (locked=true)
  - dodaje event do outbox
  - probuje wyslac do Reporting API (2xx = sukces)
```

BUG/ASO po potwierdzeniu sa zablokowane (nie mozna usunac).

### 3.4 Przycisk RAPORT

Klikniecie RAPORT:
1) Backend robi flush pending/failed z outbox
2) Generuje PDF
3) Zwraca info o PDF

Frontend nie pokazuje procesu flush.

---

## 4. API Backend

### 4.1 Endpointy

| Metoda | Sciezka | Opis |
|--------|---------|------|
| GET | `/api/reports` | Lista buildow |
| GET | `/api/reports/{id}/results` | Wyniki testow |
| GET | `/api/reports/{id}/image/ref` | Obraz referencyjny |
| GET | `/api/builds/{id}/state` | state.json (test_cases + outbox) |
| POST | `/api/builds/{id}/events` | BUG_SET / ASO_SET |
| POST | `/api/builds/{id}/lock/acquire` | Soft-lock builda |
| POST | `/api/builds/{id}/lock/heartbeat` | Heartbeat locka |
| POST | `/api/builds/{id}/lock/release` | Release locka |
| POST | `/api/builds/{id}/report` | Flush + PDF |
| POST | `/api/reports/{id}/baseline/challenge` | Challenge dla baseline |
| POST | `/api/reports/{id}/baseline/send` | Wyslanie baseline |

### 4.2 Payload eventu

```javascript
{
  event_id: "uuid",
  type: "BUG_SET" | "ASO_SET",
  test_case_id: "scenario_id::actual_path::baseline_path::diff_path",
  payload: {
    note: "optional <= 200"
  }
}
```

`note` z prompta BUG/ASO jest przechowywana w stanie przypadku testowego (osobno dla BUG i ASO).

---

## 5. Bezpieczenstwo

- wszystkie pola tekstowe <= 500 znakow
- tekst traktowany jako nieufny
- renderowanie tylko przez escaped moustache (bez `dangerouslySetInnerHTML`)
- brak interpolacji do komend systemowych
- walidacja build_id
- PDF oparty o dane z escaped plain text

---

## 6. Klawisze i auto-repeat

- wszystkie skroty ignoruja auto-repeat
- wymagany keyup przed kolejna akcja
- LSHIFT nie moze powodowac kaskadowego wyjscia z prompta/modala/raportu

---

## 7. Testy

Testy jednostkowe sa w `.test.js`, testy backendu w `qa/aso/...`.

```bash
npm run test:unit
npm run test:coverage
npm run build
```

---

## 8. Zalezne pliki

| Plik | Opis |
|------|------|
| `bug_report_pdf_config.json` | konfiguracja PDF |
| `vite.config.js` | konfiguracja bundlera |
| `vitest.config.js` | konfiguracja testow |
| `i18n/locales/{en,pl,uk}.json` | tlumaczenia |
