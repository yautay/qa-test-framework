# CR Audit Prompt (Python)

Poniższy prompt jest przeznaczony do automatycznego code review w Bitbucket dla tego repozytorium (Python/pytest/Playwright). Skopiuj całość do agenta CR.

```text
Spójrz na to. Zrób audyt zmian bieżącej gałęzi vs TARGET_BRANCH.
Sprawdź: wzorce projektowe, bezpieczeństwo (OWASP Top 10), wydajność oraz sensowne refaktory w bliskim sąsiedztwie zmian.
Kontekst: przed audytem odczytaj pyproject.toml i ustal wersję Pythona oraz używane biblioteki i ich wersje; oceniaj zmiany z uwzględnieniem tego stacku.

Zasady:
- Refaktory tylko proporcjonalne do skali zmian; bez sugestii "na siłę".
- Przy małych zmianach proponuj tylko małe i szybkie poprawki.
- Bezpieczeństwo: walidacja wejścia, autoryzacja endpointów, SQL injection, XSS, SSRF, CSRF, path traversal, deserializacja, logowanie danych wrażliwych.
- Wydajność: czas requestów/procesów, DB/N+1, zbędne I/O, niepotrzebne alokacje.

Format odpowiedzi (zwięźle):
- Sekcja "Wyniki" posortowana wg severity: Critical, High, Medium, Low.
- Każdy wynik w osobnym bloku i w osobnych liniach:
  **Severity**: <Critical|High|Medium|Low>
  **Tytuł**: <krotki tytul>
  **Lokalizacja**: <path:linia>
  **Opis**: <krotki opis ryzyka>
  **Rekomendacja**: <konkretna rekomendacja>
- Oddzielaj kolejne wyniki horyzontalnym separatorem.
- Gdy brak problemów: "Brak wyników".
- Sekcja "Możliwe refaktory" (max 3, łatwe i mało czasochłonne).

Decyzja:
- Jeśli istnieje >=1 finding Critical lub High -> result -> fail
- W przeciwnym razie -> result -> ok
- Ostatnia linia MUSI być dokładnie jedna z poniższych:
result -> ok
result -> fail
```
