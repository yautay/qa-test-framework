from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    numprocesses = getattr(config.option, "numprocesses", None)
    try:
        workers = int(numprocesses or 0)
    except (TypeError, ValueError):
        workers = 0

    if workers > 1:
        raise pytest.UsageError(
            "Setup suite qa/e2e/netcorner/setup/tests musi dzialac szeregowo. "
            "Uruchom bez xdist albo z -n 1."
        )
