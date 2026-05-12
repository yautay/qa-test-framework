from __future__ import annotations

import re

from playwright.sync_api import Locator


def get_visible_text(locator: Locator) -> str:
    element = locator.first
    if element.count() == 0 or not element.is_visible():
        return ""
    return (element.text_content() or "").strip()


def strip_prefix(text: str, prefix: str) -> str:
    return text.removeprefix(prefix).strip()


def normalize_price(text: str) -> str:
    match = re.search(r"([\d\s]+(?:[\.,]\d{2})?)", text)
    if match:
        return match.group(1).replace(" ", "")
    return text


def price_text_to_float(text: str) -> float:
    """Convert a raw price string (e.g. '1 599,99 zł') to a comparable float."""
    normalized = normalize_price(text)
    if not normalized:
        return 0.0
    return float(normalized.replace(",", ".").replace(" ", ""))
