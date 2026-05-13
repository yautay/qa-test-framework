from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest

from framework.browser.session import (
    BrowserSession,
    _create_selenium_session_for_cdp,
    _extract_webdriver_error_details,
    close_browser_session,
    open_browser_session,
)
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
        self.connect_over_cdp_calls: list[dict[str, object]] = []

    def launch(self, **kwargs):
        self.launch_calls.append(dict(kwargs))
        return _FakeBrowser()

    def connect(self, endpoint: str, **kwargs):
        self.connect_calls.append({"endpoint": endpoint, **kwargs})
        return _FakeBrowser()

    def connect_over_cdp(self, endpoint: str, **kwargs):
        self.connect_over_cdp_calls.append({"endpoint": endpoint, **kwargs})
        return _FakeBrowser()


class _FakePlaywright:
    def __init__(self) -> None:
        self.chromium = _FakeBrowserType()
        self.firefox = _FakeBrowserType()


class _FakeResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status={self.status_code}")

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeCdpBrowser:
    def close(self) -> None:
        return None


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


def test_open_browser_session_auto_falls_back_to_selenium_cdp(monkeypatch: pytest.MonkeyPatch) -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="auto",
        grid_ws_endpoint="http://10.0.0.10:4444",
        browser="chromium",
    )
    playwright = _FakePlaywright()
    expected = BrowserSession(
        browser=cast(Any, _FakeBrowser()),
        provider="selenium_cdp",
        endpoint="http://10.0.0.10:9222",
        selenium_session_id="abc",
        selenium_grid_url="http://10.0.0.10:4444",
    )

    def _raise_playwright(*_args, **_kwargs):
        raise RuntimeError("not a playwright endpoint")

    monkeypatch.setattr("framework.browser.session._connect_playwright_grid", _raise_playwright)
    monkeypatch.setattr("framework.browser.session._connect_selenium_cdp_grid", lambda *_args, **_kwargs: expected)

    session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "selenium_cdp"
    assert session.endpoint == "http://10.0.0.10:9222"


def test_open_browser_session_allows_selenium_cdp_with_explicit_cdp_endpoint_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="selenium_cdp",
        grid_ws_endpoint="",
        grid_cdp_endpoint="ws://10.0.0.10:9222/devtools/browser/abc",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    session = open_browser_session(cast(Any, playwright), env)

    assert session.provider == "selenium_cdp"
    assert playwright.chromium.connect_over_cdp_calls[0]["endpoint"] == "ws://10.0.0.10:9222/devtools/browser/abc"


def test_open_browser_session_rejects_selenium_cdp_without_any_endpoint() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="selenium_cdp",
        grid_ws_endpoint="",
        grid_cdp_endpoint="",
        browser="chromium",
    )
    playwright = _FakePlaywright()

    with pytest.raises(RuntimeError, match="requires GRID_CDP_ENDPOINT"):
        open_browser_session(cast(Any, playwright), env)


def test_open_browser_session_rejects_selenium_cdp_for_non_chromium_browser() -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="selenium_cdp",
        grid_ws_endpoint="http://10.0.0.10:4444",
        browser="firefox",
    )
    playwright = _FakePlaywright()

    with pytest.raises(RuntimeError, match="chromium/chrome"):
        open_browser_session(cast(Any, playwright), env)


def test_close_browser_session_closes_grid_session(monkeypatch: pytest.MonkeyPatch) -> None:
    env = replace(load_env(), grid_connect_timeout_ms=12345)
    browser = _FakeBrowser()
    session = BrowserSession(
        browser=cast(Any, browser),
        provider="selenium_cdp",
        endpoint="http://10.0.0.10:9222",
        selenium_session_id="abc",
        selenium_grid_url="http://10.0.0.10:4444",
    )
    deleted: dict[str, object] = {}

    def _fake_delete(*, grid_url: str, session_id: str, timeout_ms: int) -> None:
        deleted["grid_url"] = grid_url
        deleted["session_id"] = session_id
        deleted["timeout_ms"] = timeout_ms

    monkeypatch.setattr("framework.browser.session._delete_selenium_session", _fake_delete)

    close_browser_session(session, env)

    assert browser.closed is True
    assert deleted == {
        "grid_url": "http://10.0.0.10:4444",
        "session_id": "abc",
        "timeout_ms": 12345,
    }


def test_create_selenium_session_uses_utf8_content_type_and_extracts_cdp(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_post(url: str, json: dict[str, object], headers: dict[str, str], timeout: float):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "value": {
                    "sessionId": "s1",
                    "capabilities": {
                        "se:cdp": "ws://10.0.0.10:9222/devtools/browser/abc",
                    },
                }
            }
        )

    monkeypatch.setattr("framework.browser.session.requests.post", _fake_post)

    session_id, cdp_endpoint = _create_selenium_session_for_cdp(
        grid_url="http://10.0.0.10:4444",
        browser_name="chromium",
        headless=True,
        timeout_ms=30000,
    )

    assert session_id == "s1"
    assert cdp_endpoint == "ws://10.0.0.10:9222/devtools/browser/abc"
    assert captured["url"] == "http://10.0.0.10:4444/session"
    assert captured["headers"] == {"Content-Type": "application/json; charset=utf-8"}
    payload = captured["json"]
    assert isinstance(payload, dict)
    capabilities = payload["capabilities"]
    assert isinstance(capabilities, dict)
    always_match = capabilities["alwaysMatch"]
    assert isinstance(always_match, dict)
    chrome_options = always_match["goog:chromeOptions"]
    assert isinstance(chrome_options, dict)
    args = chrome_options["args"]
    assert isinstance(args, list)
    assert "--headless=new" in args
    assert "--no-sandbox" in args
    assert "--disable-dev-shm-usage" in args


def test_open_browser_session_retries_selenium_with_headless_on_devtoolsactiveport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="selenium_cdp",
        grid_ws_endpoint="http://10.0.0.10:4444",
        browser="chromium",
        headless=False,
    )
    playwright = _FakePlaywright()
    calls: list[bool] = []

    def _fake_create(
        *, grid_url: str, browser_name: str, headless: bool, timeout_ms: int, ws_auth_headers: object = None
    ):
        _ = (grid_url, browser_name, timeout_ms)
        calls.append(headless)
        if not headless:
            raise RuntimeError("session not created: DevToolsActivePort file doesn't exist")
        return "session-1", "ws://10.0.0.10:4444/session/session-1/se/cdp"

    monkeypatch.setattr("framework.browser.session._create_selenium_session_for_cdp", _fake_create)
    monkeypatch.setattr(
        playwright.chromium,
        "connect_over_cdp",
        lambda endpoint, **kwargs: _FakeCdpBrowser(),
    )

    session = open_browser_session(cast(Any, playwright), env)

    assert calls == [False, True]
    assert session.provider == "selenium_cdp"


def test_extract_webdriver_error_details_reads_webdriver_value_message() -> None:
    response = _FakeResponse(
        {
            "value": {
                "error": "session not created",
                "message": "Chrome failed to start",
            }
        },
        status_code=500,
    )

    details = _extract_webdriver_error_details(cast(Any, response))

    assert details == "session not created: Chrome failed to start"


def test_open_browser_session_deletes_selenium_session_when_cdp_attach_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="selenium_cdp",
        grid_ws_endpoint="http://10.0.0.10:4444",
        browser="chromium",
    )
    playwright = _FakePlaywright()
    deleted: dict[str, object] = {}

    monkeypatch.setattr(
        "framework.browser.session._create_selenium_session_for_cdp",
        lambda **_kwargs: ("session-2", "ws://10.0.0.10:4444/session/session-2/se/cdp"),
    )

    def _fake_delete(*, grid_url: str, session_id: str, timeout_ms: int, ws_auth_headers: object = None) -> None:
        deleted["grid_url"] = grid_url
        deleted["session_id"] = session_id
        deleted["timeout_ms"] = timeout_ms

    monkeypatch.setattr("framework.browser.session._delete_selenium_session", _fake_delete)
    monkeypatch.setattr(
        playwright.chromium,
        "connect_over_cdp",
        lambda endpoint, **kwargs: (_ for _ in ()).throw(RuntimeError("socket hang up")),
    )

    with pytest.raises(RuntimeError, match="could not attach to CDP endpoint"):
        open_browser_session(cast(Any, playwright), env)

    assert deleted["grid_url"] == "http://10.0.0.10:4444"
    assert deleted["session_id"] == "session-2"


def test_open_browser_session_auto_skips_invalid_selenium_fallback_for_playwright_ws_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = replace(
        load_env(),
        is_grid_available=True,
        grid_provider="auto",
        grid_ws_endpoint="ws://127.0.0.1:9323/",
        grid_cdp_endpoint="",
        browser="chromium",
    )
    playwright = _FakePlaywright()
    selenium_attempted = False

    def _raise_playwright(*_args, **_kwargs):
        raise RuntimeError("not a playwright endpoint")

    def _unexpected_selenium(*_args, **_kwargs):
        nonlocal selenium_attempted
        selenium_attempted = True
        raise AssertionError("selenium fallback should be skipped")

    monkeypatch.setattr("framework.browser.session._connect_playwright_grid", _raise_playwright)
    monkeypatch.setattr("framework.browser.session._connect_selenium_cdp_grid", _unexpected_selenium)

    with pytest.raises(RuntimeError, match="selenium_cdp=no GRID_CDP_ENDPOINT"):
        open_browser_session(cast(Any, playwright), env)

    assert selenium_attempted is False
