from __future__ import annotations

import pytest

from tools.visual.baseline_ops.minio_ops import _normalize_minio_endpoint

pytestmark = [pytest.mark.aso]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("127.0.0.1:9000", "127.0.0.1:9000"),
        ("https://minio.example.com", "minio.example.com"),
        ("http://minio.local:9000", "minio.local:9000"),
    ],
)
def test_normalize_minio_endpoint_accepts_supported_formats(raw: str, expected: str) -> None:
    assert _normalize_minio_endpoint(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "https://minio.example.com/minio",
        "https://minio.example.com?x=1",
        "https://user:pass@minio.example.com",
    ],
)
def test_normalize_minio_endpoint_rejects_path_query_and_credentials(raw: str) -> None:
    with pytest.raises(ValueError):
        _normalize_minio_endpoint(raw)
