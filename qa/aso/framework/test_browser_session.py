from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest

from framework.browser.session import GridAuthError, close_browser_session, open_browser_session
from framework.env import load_env

pytestmark = [pytest.mark.aso]


class _FakeBrowser:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FakeBrowserType:
    def __init__(self) -> None:
        self.launch_calls: list[dict[str, object]] = []
        self.connect_calls: list[dict[str, object]] = []

    def launch(self, **kwargs):
        self.launch_calls.append(dict(kwargs))
        return _FakeBrowser()

    def connect(self, endpoint: str, **kwargs):
        self.connect_calls.append({"endpoint": endpoint, **kwargs})
        return _FakeBrowser()


class _FakePlaywright:
    def __init__(self) -> None:
        self.chromium = _FakeBrowserType()
        self.firefox = _FakeBrowserType()


def test_open_browser_session_launches_local_browser_when_grid_disabled() -> None:
    env = replace(load_env(), is_grid_available=False, browser="chromium", headless=True)
    playwright = _FakePlaywright()

    session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "local"
    assert playwright.chromium.launch_calls == [{"headless": True}]


def test_open_browser_session_uses_playwright_provider_when_forced() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="playwright",
        grid_ws_endpoint="ws://127.0.0.1:9323/",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "playwright"
    assert playwright.chromium.connect_calls[0]["endpoint"] == "ws://127.0.0.1:9323/"


def test_open_browser_session_normalizes_playwright_ws_endpoint_with_trailing_slash() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="playwright",
        grid_ws_endpoint="ws://127.0.0.1:9323/pw-ws",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "playwright"
    assert session.endpoint == "ws://127.0.0.1:9323/pw-ws/"
    assert playwright.chromium.connect_calls[0]["endpoint"] == "ws://127.0.0.1:9323/pw-ws/"


def test_open_browser_session_normalizes_playwright_wss_endpoint_and_preserves_query() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="playwright",
        grid_ws_endpoint="wss://127.0.0.1:9323/pw-ws?foo=1",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "playwright"
    assert session.endpoint == "wss://127.0.0.1:9323/pw-ws/?foo=1"
    assert playwright.chromium.connect_calls[0]["endpoint"] == "wss://127.0.0.1:9323/pw-ws/?foo=1"


def test_open_browser_session_warns_for_playwright_http_endpoint() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="playwright",
        grid_ws_endpoint="http://127.0.0.1:9323/pw-ws",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    with pytest.warns(RuntimeWarning, match="GRID_PROVIDER=playwright"):
        session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "playwright"
    assert session.endpoint == "http://127.0.0.1:9323/pw-ws"
    assert playwright.chromium.connect_calls[0]["endpoint"] == "http://127.0.0.1:9323/pw-ws"


def test_open_browser_session_rejects_non_playwright_grid_provider() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="auto",
        grid_ws_endpoint="ws://127.0.0.1:9323/",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    with pytest.raises(RuntimeError, match="Supported values: playwright"):
        open_browser_session(cast(Any, playwright), env)


def test_open_browser_session_raises_grid_auth_error_on_401() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="playwright",
        grid_ws_endpoint="ws://127.0.0.1:9323/",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    def _raise_unauthorized(_endpoint: str, **_kwargs):
        raise RuntimeError("401 Unauthorized")

    playwright.chromium.connect = _raise_unauthorized  # type: ignore[method-assign]

    with pytest.raises(GridAuthError, match="401 Unauthorized"):
        open_browser_session(cast(Any, playwright), env)


def test_close_browser_session_closes_browser_only() -> None:
    env = replace(load_env(), grid_connect_timeout_ms=12345)
    browser = _FakeBrowser()
    session = replace(
        open_browser_session(
            cast(Any, _FakePlaywright()),
            replace(load_env(), is_grid_available=False, browser="chromium", headless=True),
        ),
        browser=cast(Any, browser),
    )

    close_browser_session(session, env)

    assert browser.closed is True
