from __future__ import annotations

from warnings import deprecated

"""Minimal helpers expressing expectations with friendly error messages."""


@deprecated("Use pytest implementation instead")
def expect_true(value: bool, message: str) -> None:
    """Assert the provided boolean is True, surfacing the supplied message on failure."""
    if not value:
        raise AssertionError(message)


@deprecated("Use pytest implementation instead")
def expect_equal(actual, expected, message: str = "") -> None:
    """Fail fast when objects differ, emitting the comparison results."""
    if actual != expected:
        raise AssertionError(message or f"Expected {expected!r}, got {actual!r}")
