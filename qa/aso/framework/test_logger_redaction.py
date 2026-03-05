from __future__ import annotations

import pytest

from framework.logger import _redact_text, _redact_value


pytestmark = [pytest.mark.aso]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Authorization=Bearer abc123", "Authorization=***REDACTED*** ***REDACTED***"),
        ("token:super-secret", "token=***REDACTED***"),
        ("https://user:pass@example.com/api", "https://***REDACTED***:***REDACTED***@example.com/api"),
    ],
)
def test_redact_text_masks_common_secret_patterns(raw: str, expected: str) -> None:
    assert _redact_text(raw) == expected


def test_redact_value_masks_sensitive_keys_recursively() -> None:
    payload = {
        "token": "abc",
        "nested": {
            "Authorization": "Bearer xyz",
            "list": ["password=hunter2", {"api_key": "key-123"}],
        },
        "safe": "hello",
    }

    redacted = _redact_value(payload)

    assert redacted["token"] == "***REDACTED***"
    assert redacted["nested"]["Authorization"] == "***REDACTED***"
    assert redacted["nested"]["list"][0] == "password=***REDACTED***"
    assert redacted["nested"]["list"][1]["api_key"] == "***REDACTED***"
    assert redacted["safe"] == "hello"
