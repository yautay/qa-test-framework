from __future__ import annotations


def expect_true(value: bool, message: str) -> None:
    assert value, message


def expect_equal(actual, expected, message: str = "") -> None:
    assert actual == expected, message or f"Expected {expected}, got {actual}"
