from __future__ import annotations

import pytest

from qa.api.lib.api_interface import ApiInterface


@pytest.fixture(scope="session")
def api_client(runtime_env):
    """HTTP API client configured from runtime environment base_url."""
    return ApiInterface(
        base_url=runtime_env.base_url,
        verify_ssl=not runtime_env.ignore_https_errors,
    )
