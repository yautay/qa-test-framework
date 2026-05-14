from __future__ import annotations

import base64
import warnings
from dataclasses import dataclass
import secrets
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import Browser, Playwright

from framework.env import RuntimeEnv


@dataclass(frozen=True)
class BrowserSession:
    browser: Browser
    provider: str
    endpoint: str


class GridAuthError(RuntimeError):
    """Raised when Grid rejects a connection with a 401 Unauthorized response."""


def _build_grid_auth_headers(auth_mode: str, username: str, password: str, token: str) -> dict[str, str]:
    """Return Authorization header dict for the given auth mode, or empty dict for 'none'."""
    headers: dict[str, str] = {
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Sec-WebSocket-Version": "13",
        # RFC6455 requires a fresh random key for each websocket handshake.
        "Sec-WebSocket-Key": base64.b64encode(secrets.token_bytes(16)).decode("ascii"),
    }
    mode = (auth_mode or "none").strip().lower()
    if mode == "basic":
        user = (username or "").strip()
        secret = (password or "").strip()
        if user and secret:
            raw = f"{user}:{secret}"
            encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded}"
    elif mode == "token":
        tok = (token or "").strip()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
    return headers


def _normalize_playwright_ws_endpoint(endpoint: str) -> str:
    """Normalize ws/wss endpoint paths to avoid redirect-only slash fixes on the server."""
    token = endpoint.strip()
    if not token:
        return token

    parsed = urlsplit(token)
    if parsed.scheme not in {"ws", "wss"}:
        return token

    path = parsed.path or ""
    if not path or path == "/" or path.endswith("/"):
        return token

    return urlunsplit((parsed.scheme, parsed.netloc, f"{path}/", parsed.query, parsed.fragment))


def _warn_if_playwright_provider_uses_http_endpoint(provider: str, endpoint: str) -> None:
    """Warn when GRID_PROVIDER=playwright is configured with an HTTP discovery URL."""
    if provider.strip().lower() != "playwright":
        return

    scheme = urlsplit(endpoint.strip()).scheme.lower()
    if scheme not in {"http", "https"}:
        return

    warnings.warn(
        "GRID_PROVIDER=playwright is using GRID_WS_ENDPOINT with HTTP(S) scheme. "
        "Prefer ws:// or wss:// to avoid discovery/auth redirect issues.",
        RuntimeWarning,
        stacklevel=3,
    )


def open_browser_session(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    if not runtime_env.is_grid_available:
        return _launch_local_browser(playwright_instance, runtime_env)

    provider = runtime_env.grid_provider.strip().lower()
    if provider == "playwright":
        if not runtime_env.grid_ws_endpoint.strip():
            raise RuntimeError("GRID_PROVIDER=playwright requires GRID_WS_ENDPOINT")
        return _connect_playwright_grid(playwright_instance, runtime_env)

    raise RuntimeError(
        f"Unsupported GRID_PROVIDER={runtime_env.grid_provider!r}. Supported values: playwright"
    )


def close_browser_session(session: BrowserSession, runtime_env: RuntimeEnv) -> None:
    _ = runtime_env
    session.browser.close()


def _launch_local_browser(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    if runtime_env.browser == "chrome":
        browser = playwright_instance.chromium.launch(channel="chrome", headless=runtime_env.headless)
        return BrowserSession(browser=browser, provider="local", endpoint="chrome")

    browser_type = getattr(playwright_instance, runtime_env.browser)
    browser = browser_type.launch(headless=runtime_env.headless)
    return BrowserSession(browser=browser, provider="local", endpoint=runtime_env.browser)


def _connect_playwright_grid(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    browser_name = "chromium" if runtime_env.browser == "chrome" else runtime_env.browser
    browser_type = getattr(playwright_instance, browser_name)
    ws_endpoint = _normalize_playwright_ws_endpoint(runtime_env.grid_ws_endpoint)
    _warn_if_playwright_provider_uses_http_endpoint(runtime_env.grid_provider, ws_endpoint)
    ws_auth_headers = _build_grid_auth_headers(
        runtime_env.grid_ws_auth_mode,
        runtime_env.grid_ws_username,
        runtime_env.grid_ws_password,
        runtime_env.grid_ws_token,
    )
    try:
        browser = browser_type.connect(
            ws_endpoint,
            timeout=runtime_env.grid_connect_timeout_ms,
            headers=ws_auth_headers or None,
        )
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "unauthorized" in msg.lower():
            raise GridAuthError(
                f"Grid connection refused (401 Unauthorized). "
                f"Check grid_ws_auth_mode, grid_ws_username/grid_ws_password or grid_ws_token "
                f"in settings.py (or env vars GRID_WS_AUTH_MODE / GRID_WS_USERNAME / GRID_WS_TOKEN). "
                f"Original error: {exc}"
            ) from exc
        raise
    return BrowserSession(browser=browser, provider="playwright", endpoint=ws_endpoint)
