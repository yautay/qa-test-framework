"""Globalne stałe timeoutów Playwright i HTTP dla całego E2E suite.

Hierarchia (tier → stała → wartość):

    A  QUICK_PROBE_MS      2_000 ms  Szybki non-blocking probe: iteracja wierszy,
                                     sprawdzenie widoczności elementu który może
                                     nie istnieć, krótkie opóźnienie po kliknięciu.

    B  ELEMENT_VISIBLE_MS  5_000 ms  Element powinien pojawić się po interakcji:
                                     otwarcie dialogu/overlay, city-select, toast.

    C  UI_ACTION_MS       15_000 ms  Standardowa akcja UI: ładowanie strony,
                                     wait_for_url, ukrycie overlay, settle AJAX,
                                     wait_for_load_state.

    D  SLOW_OPERATION_MS  30_000 ms  Wolne operacje: duże tabele (promotions tab),
                                     strona TYP po złożeniu zamówienia.

Per-projektowe moduły (qa/e2e/netcorner/<project>/lib/timeouts.py) importują
te wartości i mogą je przeciążyć dla specyfiki projektu.

Wyjątki (nie należą do powyższej hierarchii, mają własne moduły):
    _REINDEX_TIMEOUT_MS                   = 120_000  (admin_wrappers.py)
    _PROMOTION_SERVICE_ACTIVATION_WAIT_MS = 120_000  (setup_flows.py)
    _MAILHOG_LOOKUP_TIMEOUT_MS            =  45_000  (inbox_flow.py)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Playwright timeouts (ms)
# ---------------------------------------------------------------------------

QUICK_PROBE_MS: int = 2_000
"""Tier A — szybki probe widoczności/tekstu; iteracja wierszy skrzynki/tabeli."""

ELEMENT_VISIBLE_MS: int = 5_000
"""Tier B — element oczekiwany po interakcji: dialog, overlay, toast, city-select."""

UI_ACTION_MS: int = 15_000
"""Tier C — standardowa akcja UI: load state, wait_for_url, overlay hide, AJAX."""

SLOW_OPERATION_MS: int = 30_000
"""Tier D — wolne operacje: duże tabele w adminie, TYP page po submicie zamówienia."""

# ---------------------------------------------------------------------------
# HTTP timeouts (s — nie ms, dla urllib / requests)
# ---------------------------------------------------------------------------

HTTP_REQUEST_TIMEOUT_S: int = 30
"""Timeout dla urllib.request.urlopen i requests.get (sekundy)."""

__all__ = [
    "QUICK_PROBE_MS",
    "ELEMENT_VISIBLE_MS",
    "UI_ACTION_MS",
    "SLOW_OPERATION_MS",
    "HTTP_REQUEST_TIMEOUT_S",
]
