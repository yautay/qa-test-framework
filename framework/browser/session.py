from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import requests
from playwright.sync_api import Browser, Playwright

from framework.env import RuntimeEnv


@dataclass(frozen=True)
class BrowserSession:
    browser: Browser
    provider: str
    endpoint: str
    selenium_session_id: str = ""
    selenium_grid_url: str = ""


class GridAuthError(RuntimeError):
    """Raised when Grid rejects a connection with a 401 Unauthorized response."""


def _build_grid_auth_headers(auth_mode: str, username: str, password: str, token: str) -> dict[str, str]:
    """Return Authorization header dict for the given auth mode, or empty dict for 'none'."""
    headers: dict[str, str] = {
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Sec-WebSocket-Version": "13",
        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
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


def open_browser_session(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    if not runtime_env.is_grid_available:
        return _launch_local_browser(playwright_instance, runtime_env)

    provider = runtime_env.grid_provider.strip().lower()
    if provider == "playwright":
        if not runtime_env.grid_ws_endpoint.strip():
            raise RuntimeError("GRID_PROVIDER=playwright requires GRID_WS_ENDPOINT")
        return _connect_playwright_grid(playwright_instance, runtime_env)
    if provider == "selenium_cdp":
        if not _can_attempt_selenium_cdp(runtime_env):
            raise RuntimeError(
                "GRID_PROVIDER=selenium_cdp requires GRID_CDP_ENDPOINT, a direct CDP GRID_WS_ENDPOINT, "
                "or an HTTP(S) Selenium Grid URL"
            )
        return _connect_selenium_cdp_grid(playwright_instance, runtime_env)
    if provider == "auto":
        if not runtime_env.grid_ws_endpoint.strip() and not runtime_env.grid_cdp_endpoint.strip():
            raise RuntimeError("GRID_PROVIDER=auto requires GRID_WS_ENDPOINT or GRID_CDP_ENDPOINT")
        return _connect_auto_grid(playwright_instance, runtime_env)

    raise RuntimeError(
        f"Unsupported GRID_PROVIDER={runtime_env.grid_provider!r}. Supported values: auto, playwright, selenium_cdp"
    )


def close_browser_session(session: BrowserSession, runtime_env: RuntimeEnv) -> None:
    browser_close_error: Exception | None = None
    selenium_close_error: Exception | None = None

    try:
        session.browser.close()
    except Exception as exc:  # pragma: no cover - depends on remote/browser lifecycle
        browser_close_error = exc

    if session.selenium_session_id and session.selenium_grid_url:
        try:
            _delete_selenium_session(
                grid_url=session.selenium_grid_url,
                session_id=session.selenium_session_id,
                timeout_ms=runtime_env.grid_connect_timeout_ms,
            )
        except Exception as exc:  # pragma: no cover - depends on remote/grid lifecycle
            selenium_close_error = exc

    if browser_close_error and selenium_close_error:
        raise RuntimeError("Failed to close both Playwright browser and Selenium Grid session") from browser_close_error
    if browser_close_error:
        raise browser_close_error
    if selenium_close_error:
        raise selenium_close_error


def _launch_local_browser(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    if runtime_env.browser == "chrome":
        browser = playwright_instance.chromium.launch(channel="chrome", headless=runtime_env.headless)
        return BrowserSession(browser=browser, provider="local", endpoint="chrome")

    browser_type = getattr(playwright_instance, runtime_env.browser)
    browser = browser_type.launch(headless=runtime_env.headless)
    return BrowserSession(browser=browser, provider="local", endpoint=runtime_env.browser)


def _connect_auto_grid(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    errors: list[str] = []

    if runtime_env.grid_ws_endpoint.strip():
        try:
            return _connect_playwright_grid(playwright_instance, runtime_env)
        except Exception as exc:
            errors.append(f"playwright={exc}")
    else:
        errors.append("playwright=GRID_WS_ENDPOINT is empty")

    if _can_attempt_selenium_cdp(runtime_env):
        try:
            return _connect_selenium_cdp_grid(playwright_instance, runtime_env)
        except Exception as exc:
            errors.append(f"selenium_cdp={exc}")
    else:
        errors.append(
            "selenium_cdp=no GRID_CDP_ENDPOINT and GRID_WS_ENDPOINT is neither "
            "a direct CDP endpoint nor an HTTP(S) Grid URL"
        )

    joined_errors = "; ".join(errors)
    raise RuntimeError(
        "GRID_PROVIDER=auto could not establish remote connection. "
        f"Endpoint={runtime_env.grid_ws_endpoint!r}. Attempts: {joined_errors}"
    )


def _connect_playwright_grid(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    browser_name = "chromium" if runtime_env.browser == "chrome" else runtime_env.browser
    browser_type = getattr(playwright_instance, browser_name)
    ws_auth_headers = _build_grid_auth_headers(
        runtime_env.grid_ws_auth_mode,
        runtime_env.grid_ws_username,
        runtime_env.grid_ws_password,
        runtime_env.grid_ws_token,
    )
    try:
        browser = browser_type.connect(
            runtime_env.grid_ws_endpoint,
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
    return BrowserSession(browser=browser, provider="playwright", endpoint=runtime_env.grid_ws_endpoint)


def _connect_selenium_cdp_grid(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> BrowserSession:
    browser_name = runtime_env.browser.strip().lower()
    if browser_name not in {"chromium", "chrome"}:
        raise RuntimeError("selenium_cdp provider supports only chromium/chrome browser")

    cdp_endpoint = runtime_env.grid_cdp_endpoint.strip()
    selenium_session_id = ""
    selenium_grid_url = ""

    ws_auth_headers = _build_grid_auth_headers(
        runtime_env.grid_ws_auth_mode,
        runtime_env.grid_ws_username,
        runtime_env.grid_ws_password,
        runtime_env.grid_ws_token,
    )
    cdp_auth_headers = _build_grid_auth_headers(
        runtime_env.grid_cdp_auth_mode,
        runtime_env.grid_cdp_username,
        runtime_env.grid_cdp_password,
        runtime_env.grid_cdp_token,
    )

    if not cdp_endpoint:
        if _is_direct_cdp_endpoint(runtime_env.grid_ws_endpoint):
            cdp_endpoint = runtime_env.grid_ws_endpoint
        else:
            selenium_grid_url = _normalize_grid_url(runtime_env.grid_ws_endpoint)
            try:
                selenium_session_id, cdp_endpoint = _create_selenium_session_for_cdp(
                    grid_url=selenium_grid_url,
                    browser_name=browser_name,
                    headless=runtime_env.headless,
                    timeout_ms=runtime_env.grid_connect_timeout_ms,
                    ws_auth_headers=ws_auth_headers,
                )
            except RuntimeError as exc:
                if runtime_env.headless or not _looks_like_chrome_startup_failure(str(exc)):
                    raise
                selenium_session_id, cdp_endpoint = _create_selenium_session_for_cdp(
                    grid_url=selenium_grid_url,
                    browser_name=browser_name,
                    headless=True,
                    timeout_ms=runtime_env.grid_connect_timeout_ms,
                    ws_auth_headers=ws_auth_headers,
                )

    try:
        browser = playwright_instance.chromium.connect_over_cdp(
            cdp_endpoint,
            timeout=runtime_env.grid_connect_timeout_ms,
            headers=cdp_auth_headers or None,
        )
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "unauthorized" in msg.lower():
            if selenium_session_id and selenium_grid_url:
                try:
                    _delete_selenium_session(
                        grid_url=selenium_grid_url,
                        session_id=selenium_session_id,
                        timeout_ms=runtime_env.grid_connect_timeout_ms,
                        ws_auth_headers=ws_auth_headers,
                    )
                except Exception:
                    pass
            raise GridAuthError(
                f"Grid CDP connection refused (401 Unauthorized). "
                f"Check grid_cdp_auth_mode, grid_cdp_username/grid_cdp_password or grid_cdp_token "
                f"in settings.py (or env vars GRID_CDP_AUTH_MODE / GRID_CDP_USERNAME / GRID_CDP_TOKEN). "
                f"Original error: {exc}"
            ) from exc
        if selenium_session_id and selenium_grid_url:
            try:
                _delete_selenium_session(
                    grid_url=selenium_grid_url,
                    session_id=selenium_session_id,
                    timeout_ms=runtime_env.grid_connect_timeout_ms,
                    ws_auth_headers=ws_auth_headers,
                )
            except Exception:
                pass
        raise RuntimeError(
            "Selenium CDP session was created but Playwright could not attach to CDP endpoint. "
            f"CDP endpoint={cdp_endpoint!r}. Original error: {exc}. "
            "This usually means Selenium Grid does not proxy websocket upgrades on /se/cdp."
        ) from exc
    return BrowserSession(
        browser=browser,
        provider="selenium_cdp",
        endpoint=cdp_endpoint,
        selenium_session_id=selenium_session_id,
        selenium_grid_url=selenium_grid_url,
    )


def _is_direct_cdp_endpoint(endpoint: str) -> bool:
    token = endpoint.strip().lower()
    return "/devtools/browser/" in token or "/se/cdp" in token or ":9222" in token


def _is_http_grid_url(endpoint: str) -> bool:
    token = endpoint.strip().lower()
    return token.startswith("http://") or token.startswith("https://")


def _can_attempt_selenium_cdp(runtime_env: RuntimeEnv) -> bool:
    if runtime_env.grid_cdp_endpoint.strip():
        return True
    grid_ws_endpoint = runtime_env.grid_ws_endpoint.strip()
    return _is_direct_cdp_endpoint(grid_ws_endpoint) or _is_http_grid_url(grid_ws_endpoint)


def _normalize_grid_url(endpoint: str) -> str:
    return endpoint.rstrip("/")


def _create_selenium_session_for_cdp(
    *,
    grid_url: str,
    browser_name: str,
    headless: bool,
    timeout_ms: int,
    ws_auth_headers: dict[str, str] | None = None,
) -> tuple[str, str]:
    always_match: dict[str, Any] = {
        "browserName": "chrome" if browser_name == "chromium" else browser_name,
        "goog:chromeOptions": {
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        },
    }
    if headless:
        chrome_options = always_match.get("goog:chromeOptions")
        if isinstance(chrome_options, dict):
            args_value = chrome_options.get("args")
            if isinstance(args_value, list):
                args_value.append("--headless=new")

    payload = {
        "capabilities": {
            "alwaysMatch": always_match,
            "firstMatch": [{}],
        }
    }
    timeout_seconds = max(timeout_ms / 1000.0, 1.0)
    request_headers = {"Content-Type": "application/json; charset=utf-8"}
    if ws_auth_headers:
        request_headers.update(ws_auth_headers)
    response = requests.post(
        f"{grid_url}/session",
        json=payload,
        headers=request_headers,
        timeout=timeout_seconds,
    )
    if response.status_code == 401:
        raise GridAuthError(
            "Selenium Grid session creation refused (401 Unauthorized). "
            "Check grid_ws_auth_mode, grid_ws_username/grid_ws_password or grid_ws_token "
            "in settings.py (or env vars GRID_WS_AUTH_MODE / GRID_WS_USERNAME / GRID_WS_TOKEN)."
        )
    if response.status_code >= 400:
        error_details = _extract_webdriver_error_details(response)
        raise RuntimeError(f"Selenium Grid session creation failed (status={response.status_code}): {error_details}")

    response_payload = response.json()
    value = response_payload.get("value") if isinstance(response_payload, dict) else None
    session_id = ""
    if isinstance(response_payload, dict):
        session_id = str(response_payload.get("sessionId") or "").strip()
    if not session_id and isinstance(value, dict):
        session_id = str(value.get("sessionId") or "").strip()
    if not session_id:
        raise RuntimeError("Could not resolve Selenium session id from Grid response")

    cdp_endpoint = _extract_cdp_endpoint_from_payload(
        response_payload, grid_url=grid_url, session_id=session_id, ws_auth_headers=ws_auth_headers
    )
    if not cdp_endpoint:
        _delete_selenium_session(
            grid_url=grid_url, session_id=session_id, timeout_ms=timeout_ms, ws_auth_headers=ws_auth_headers
        )
        raise RuntimeError(
            "Could not resolve CDP endpoint from Selenium Grid session capabilities. "
            "Set GRID_CDP_ENDPOINT explicitly or ensure Grid exposes se:cdp/debuggerAddress."
        )
    return session_id, cdp_endpoint


def _extract_cdp_endpoint_from_payload(
    payload: dict[str, Any],
    *,
    grid_url: str,
    session_id: str,
    ws_auth_headers: dict[str, str] | None = None,
) -> str:
    value = payload.get("value") if isinstance(payload, dict) else None
    capabilities = value.get("capabilities") if isinstance(value, dict) else None
    if not isinstance(capabilities, dict):
        capabilities = {}

    for key in ("se:cdp", "se:cdpEndpoint"):
        endpoint = str(capabilities.get(key) or "").strip()
        if endpoint:
            return endpoint

    chrome_options = capabilities.get("goog:chromeOptions")
    if isinstance(chrome_options, dict):
        debugger_address = str(chrome_options.get("debuggerAddress") or "").strip()
        if debugger_address:
            if debugger_address.startswith("http://") or debugger_address.startswith("https://"):
                return debugger_address
            return f"http://{debugger_address}"

    endpoint = _try_get_grid_cdp_endpoint(grid_url=grid_url, session_id=session_id, ws_auth_headers=ws_auth_headers)
    return endpoint.strip()


def _try_get_grid_cdp_endpoint(
    *, grid_url: str, session_id: str, ws_auth_headers: dict[str, str] | None = None
) -> str:
    response = requests.get(
        f"{grid_url}/session/{session_id}/se/cdp",
        headers=ws_auth_headers or {},
        timeout=5,
    )
    if response.status_code >= 400:
        return ""
    payload = response.json()
    if not isinstance(payload, dict):
        return ""
    value = payload.get("value")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("cdp", "endpoint", "wsUrl", "url"):
            token = str(value.get(key) or "").strip()
            if token:
                return token
    return ""


def _delete_selenium_session(
    *, grid_url: str, session_id: str, timeout_ms: int, ws_auth_headers: dict[str, str] | None = None
) -> None:
    timeout_seconds = max(timeout_ms / 1000.0, 1.0)
    response = requests.delete(
        f"{grid_url}/session/{session_id}",
        headers=ws_auth_headers or {},
        timeout=timeout_seconds,
    )
    if response.status_code in (404, 410):
        return
    response.raise_for_status()


def _extract_webdriver_error_details(response: requests.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return response.text.strip() or "unknown error"

    if not isinstance(payload, dict):
        return str(payload)
    value = payload.get("value")
    if isinstance(value, dict):
        message = str(value.get("message") or "").strip()
        error = str(value.get("error") or "").strip()
        if error and message:
            return f"{error}: {message}"
        if message:
            return message
        if error:
            return error
    return str(payload)


def _looks_like_chrome_startup_failure(error_message: str) -> bool:
    token = error_message.lower()
    return "devtoolsactiveport" in token or "chrome failed to start" in token
