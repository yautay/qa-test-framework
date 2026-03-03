from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api]


def test_health(api_client):
    if not api_client.base_url:
        pytest.skip("BASE_URL not set")
    response = api_client.get("/health")
    assert response.status_code < 500
