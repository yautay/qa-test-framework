from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--viewport",
        action="store",
        default="fhd",
        choices=("mobile", "tablet", "fhd", "2k", "4k"),
        help="Viewport preset for browser context: mobile|tablet|fhd|2k|4k (default: fhd)",
    )
    parser.addoption(
        "--visual-approve",
        action="store_true",
        default=False,
        help="Approve current visual screenshots as new baseline",
    )
    parser.addoption(
        "--visual-scenario",
        action="store",
        default="",
        help="Run only visual scenarios matching substring",
    )
    parser.addoption(
        "--visual-viewports",
        action="store",
        default="",
        help="Comma-separated visual viewport presets, e.g. mobile,tablet,fhd",
    )
