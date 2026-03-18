from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any, TypeVar

try:
    allure = importlib.import_module("allure")
except Exception:
    allure = None

T = TypeVar("T", bound=Callable[..., Any])


def step(title: str) -> Callable[[T], T]:
    """Safe allure.step decorator - does not crash when allure is not installed."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return allure.step(title)


def feature(name: str) -> Callable[[T], T]:
    """Safe allure.feature decorator."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return allure.feature(name)


def story(name: str) -> Callable[[T], T]:
    """Safe allure.story decorator."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return allure.story(name)


def severity(level: Any) -> Callable[[T], T]:
    """Safe allure.severity decorator."""
    if allure is None:

        def decorator(func: T) -> T:
            return func

        return decorator
    return allure.severity(level)
