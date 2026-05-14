from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def parse_price(raw: str | None) -> Decimal | None:
    """Convert a Polish-formatted price string to Decimal.

    Handles formats like:
        '1 234,56 zł'  → Decimal('1234.56')
        '1.234,56 zł'  → Decimal('1234.56')
        '299,99 zł'    → Decimal('299.99')
        '299'          → Decimal('299')

    Returns ``None`` if the input is ``None`` or contains no parseable number.
    Returns ``Decimal('0.00')`` if the cleaned string is present but cannot be
    converted (e.g. malformed input).
    """
    if raw is None:
        return None
    # Replace comma decimal separator with dot, then strip all non-numeric chars
    # except dots (which now represent both thousands separators and decimal point).
    cleaned = re.sub(r"[^\d,.]", "", raw.replace(",", "."))
    if not cleaned:
        return None
    # If there are multiple dots, only the last one is the decimal separator.
    parts = cleaned.rsplit(".", 1)
    normalized = parts[0].replace(".", "") + ("." + parts[1] if len(parts) == 2 else "")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return Decimal("0.00")


__all__ = ["parse_price"]
