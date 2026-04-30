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
