"""Stałe timeoutów dla projektu nuxt/pl.

Re-eksportuje globalną hierarchię z ``framework.timeouts``.
Aby przeciążyć wartość dla specyfiki projektu pl, nadpisz stałą poniżej importu.

Pełna dokumentacja hierarchii: ``framework/timeouts.py`` oraz
root ``AGENTS.md`` sekcja *Timeout Constants*.
"""

from __future__ import annotations

from framework.timeouts import (
    ELEMENT_VISIBLE_MS,
    HTTP_REQUEST_TIMEOUT_S,
    QUICK_PROBE_MS,
    SLOW_OPERATION_MS,
    UI_ACTION_MS,
)

__all__ = [
    "QUICK_PROBE_MS",
    "ELEMENT_VISIBLE_MS",
    "UI_ACTION_MS",
    "SLOW_OPERATION_MS",
    "HTTP_REQUEST_TIMEOUT_S",
]
