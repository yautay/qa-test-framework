from __future__ import annotations

"""Minimal helpers expressing expectations with friendly error messages."""


def expect_true(value: bool, message: str) -> None:
    """Assert the provided boolean is True, surfacing the supplied message on failure."""

    assert value, message


def expect_equal(actual, expected, message: str = "") -> None:
    """Fail fast when objects differ, emitting the comparison results."""

    assert actual == expected, message or f"Expected {expected}, got {actual}"
