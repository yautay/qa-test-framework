from __future__ import annotations

import pytest


def scenario(description: str):
    return pytest.mark.scenario(description)
