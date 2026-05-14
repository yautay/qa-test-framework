# Grid Basic Auth and Token Auth Implementation Plan

## Overview

Add `Authorization` header support (Basic Auth and Bearer Token) for all Grid connections — Playwright WS connect, CDP connect, and Selenium HTTP probe requests. Auth mode, credentials, and tokens are configurable per-endpoint via `settings.py` with env var override priority. Sensitive fields are masked in all repr/log output.

## Current State Analysis

- `settings.py:28-32` — Grid section has 4 fields: `grid_provider`, `grid_ws_endpoint`, `grid_cdp_endpoint`, `grid_connect_timeout_ms`. No auth fields.
- `framework/env.py:60-153` — `RuntimeEnv` is a `@dataclass(frozen=True)`. No `__repr__` override; default dataclass repr exposes **all** field values. The 4 existing sensitive fields (`jira_password`, `jira_api_token`, `visual_minio_secret_key`, `reporting_api_token`) are currently unmasked.
- `framework/env.py:223-232` — `load_env()` wires existing GRID_* fields via `env_str`/`env_int`. New auth fields follow identical pattern with `getattr(settings, ..., default)` guard (same as Jira fields at lines 472–498).
- `framework/browser/session.py:113-120` — `_connect_playwright_grid` calls `browser_type.connect(endpoint, timeout=...)` with no headers.
- `framework/browser/session.py:154-158` — `_connect_selenium_cdp_grid` calls `playwright_instance.chromium.connect_over_cdp(cdp_endpoint, timeout=...)` with no headers.
- `framework/browser/session.py:235-239` — `_create_selenium_session_for_cdp` POST uses only `Content-Type` header; 400+ raises `RuntimeError`.
- `framework/browser/session.py:288-292` — `_try_get_grid_cdp_endpoint` GET has no headers.
- `framework/browser/session.py:311-317` — `_delete_selenium_session` DELETE has no headers.
- Playwright 1.51.0 confirmed: both `connect()` and `connect_over_cdp()` accept `headers: Optional[Dict[str, str]]` kwarg (forwarded to the WebSocket upgrade HTTP request).

## Desired End State

- `settings.py` contains 8 new fields under `# Grid`: `grid_ws_auth_mode`, `grid_ws_username`, `grid_ws_password`, `grid_ws_token`, `grid_cdp_auth_mode`, `grid_cdp_username`, `grid_cdp_password`, `grid_cdp_token`.
- `RuntimeEnv` declares the 8 new fields; the 4 secret ones (`grid_ws_password`, `grid_ws_token`, `grid_cdp_password`, `grid_cdp_token`) use `dataclasses.field(repr=False)`. The 4 pre-existing unmasked secrets also get `field(repr=False)`.
- `load_env()` reads 8 new `GRID_WS_*` / `GRID_CDP_*` env vars with `getattr(settings, ..., default)` fallback.
- `session.py` has `_build_grid_auth_headers()` helper and `GridAuthError(RuntimeError)`.
- All 5 connect/probe call sites pass auth headers; 401 responses raise `GridAuthError` with actionable hint.
- `.env.example` updated with 8 new stubs after `GRID_CONNECT_TIMEOUT_MS`.
- `README-DEV.md` documents the new env vars.

### Verification:
```
HEADLESS=1 IS_GRID_AVAILABLE=0 REPORTING_ENABLED=0 ALLURE_ENABLED=0 PYTEST_HTML_ENABLED=0 RECORD_VIDEO=0 make check
```
Collection and suite must pass with zero regressions.

### Key Discoveries:
- `framework/env.py:472-498` — `getattr(settings, "field", default)` guard pattern for optional `settings.py` fields; **must** be used for all 8 new fields.
- `framework/integrations/jira/client.py:50-64` — `_auth_header()` is the exact reference for `_build_grid_auth_headers()`: `base64.b64encode` for Basic, `Bearer` prefix for token.
- `framework/browser/session.py:241-243` — existing `>=400` check raises `RuntimeError`; needs to special-case `401` to `GridAuthError`.
- `framework/browser/session.py:159-173` — CDP connect error is already caught and re-raised as `RuntimeError`; the same catch block should detect 401-like messages and raise `GridAuthError` instead.
- HTTP probe requests (`POST /session`, `GET /session/{id}/se/cdp`, `DELETE /session/{id}`) all target `grid_url` which is derived from `grid_ws_endpoint` — WS auth credentials are used for all three.

## What We're NOT Doing

- No changes to `settings_cli.py` — confirmed no GRID fields there.
- No health-check or pre-validation of credentials before connect.
- No new pip dependencies — stdlib `base64` only.
- No new tests in this ticket — test coverage is a separate ticket.
- No changes to `_connect_auto_grid` directly — it delegates to the two private functions that will be patched.
- No changes to Jira token auth behaviour (Jira uses `base64(user:api_token)` for "token" mode; Grid uses `Bearer <token>` — intentionally different per spec).

## Implementation Approach

Changes flow in dependency order: settings → RuntimeEnv → load_env → session helper → session call sites → docs. Each phase is independently verifiable with `make check`.

---

## Phase 1: Settings, RuntimeEnv, and load_env Plumbing

### Overview

Declare the 8 new auth fields in all three config layers, mask the 4 new secret fields and fix the 4 pre-existing unmasked ones.

### Changes Required

#### 1. `settings.py` — Add 8 fields under `# Grid`

**File**: `settings.py`  
**Change**: Insert after line 32 (`grid_connect_timeout_ms = 30000`):

```python
grid_ws_auth_mode = "none"   # none | basic | token
grid_ws_username = ""
grid_ws_password = ""
grid_ws_token = ""

grid_cdp_auth_mode = "none"  # none | basic | token
grid_cdp_username = ""
grid_cdp_password = ""
grid_cdp_token = ""
```

#### 2. `framework/env.py` — RuntimeEnv field declarations

**File**: `framework/env.py`  
**Change A**: Add `from dataclasses import dataclass, field` — replace the bare `from dataclasses import dataclass` import (if present) or add `field` to the import.

**Change B**: Insert 8 new field declarations after `grid_connect_timeout_ms: int` (line 69). Secret fields use `field(repr=False)`:

```python
grid_ws_auth_mode: str
grid_ws_username: str
grid_ws_password: str = field(repr=False)
grid_ws_token: str = field(repr=False)
grid_cdp_auth_mode: str
grid_cdp_username: str
grid_cdp_password: str = field(repr=False)
grid_cdp_token: str = field(repr=False)
```

**Change C**: Apply `field(repr=False)` to the 4 pre-existing unmasked sensitive fields. Update their declarations:

- Line 85: `reporting_api_token: str = field(repr=False)`
- Line 121: `visual_minio_secret_key: str = field(repr=False)`
- Line 145: `jira_password: str = field(repr=False)`
- Line 148: `jira_api_token: str = field(repr=False)`

> Note: `field(repr=False)` with no `default` still requires the value to be passed positionally at construction time — this is correct since `load_env()` always passes all fields.

#### 3. `framework/env.py` — `load_env()` wiring

**File**: `framework/env.py`  
**Change**: In the `return RuntimeEnv(...)` block, insert 8 new keyword arguments immediately after the `grid_connect_timeout_ms=...` entry (after line 232):

```python
grid_ws_auth_mode=env_str("GRID_WS_AUTH_MODE", str(getattr(settings, "grid_ws_auth_mode", "none"))).strip().lower(),
grid_ws_username=env_str("GRID_WS_USERNAME", str(getattr(settings, "grid_ws_username", ""))),
grid_ws_password=env_str("GRID_WS_PASSWORD", str(getattr(settings, "grid_ws_password", ""))),
grid_ws_token=env_str("GRID_WS_TOKEN", str(getattr(settings, "grid_ws_token", ""))),
grid_cdp_auth_mode=env_str("GRID_CDP_AUTH_MODE", str(getattr(settings, "grid_cdp_auth_mode", "none"))).strip().lower(),
grid_cdp_username=env_str("GRID_CDP_USERNAME", str(getattr(settings, "grid_cdp_username", ""))),
grid_cdp_password=env_str("GRID_CDP_PASSWORD", str(getattr(settings, "grid_cdp_password", ""))),
grid_cdp_token=env_str("GRID_CDP_TOKEN", str(getattr(settings, "grid_cdp_token", ""))),
```

### Success Criteria

#### Automated Verification:
- [x] `make check` passes (includes typecheck, lint, format-check, test-aso, verify-discovery)
- [x] `make verify-discovery` passes — collection unaffected by new RuntimeEnv fields
- [x] `make test-aso` passes — no regressions in existing ASO suite

#### Manual Verification:
- [x] `settings.py` contains all 8 new fields with `"none"` / `""` defaults
- [x] `python -c "from framework.env import load_env; e = load_env(); print(repr(e))"` — repr does not contain any of: `grid_ws_password`, `grid_ws_token`, `grid_cdp_password`, `grid_cdp_token`, `jira_password`, `jira_api_token`, `visual_minio_secret_key`, `reporting_api_token` values (fields appear as omitted from repr)
- [x] `e.grid_ws_auth_mode` resolves to `"none"` when no env var is set

---

## Phase 2: Auth Header Helper and GridAuthError

### Overview

Add the `_build_grid_auth_headers()` pure function and the `GridAuthError` exception class to `session.py`. No call sites are wired yet — this phase is isolated and testable independently.

### Changes Required

#### 1. `framework/browser/session.py` — Imports

**File**: `framework/browser/session.py`  
**Change**: Add `import base64` at the top of the file alongside existing stdlib imports (after `from __future__ import annotations`).

#### 2. `framework/browser/session.py` — GridAuthError and helper

**File**: `framework/browser/session.py`  
**Change**: Insert after the `BrowserSession` dataclass definition (after line 19), before `open_browser_session`:

```python
class GridAuthError(RuntimeError):
    """Raised when Grid rejects a connection with a 401 Unauthorized response."""


def _build_grid_auth_headers(auth_mode: str, username: str, password: str, token: str) -> dict[str, str]:
    """Return Authorization header dict for the given auth mode, or empty dict for 'none'."""
    mode = (auth_mode or "none").strip().lower()
    if mode == "basic":
        user = (username or "").strip()
        secret = (password or "").strip()
        if user and secret:
            raw = f"{user}:{secret}"
            encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
    elif mode == "token":
        tok = (token or "").strip()
        if tok:
            return {"Authorization": f"Bearer {tok}"}
    return {}
```

### Success Criteria

#### Automated Verification:
- [x] `make check` passes — typecheck confirms `dict[str, str]` return type, no import errors

#### Manual Verification:
- [x] `python -c "from framework.browser.session import _build_grid_auth_headers; print(_build_grid_auth_headers('basic','u','p',''))"` returns `{'Authorization': 'Basic dTpw'}`
- [x] `_build_grid_auth_headers('token', '', '', 'mytoken')` returns `{'Authorization': 'Bearer mytoken'}`
- [x] `_build_grid_auth_headers('none', 'u', 'p', 't')` returns `{}`

---

## Phase 3: Header Injection into All Connect/Probe Call Sites

### Overview

Wire `_build_grid_auth_headers()` into all 5 call sites and upgrade error handling to raise `GridAuthError` on 401.

### Changes Required

#### 1. `_connect_playwright_grid` — WS connect (session.py:116-119)

**File**: `framework/browser/session.py`  
**Change**: Build WS auth headers before the connect call and pass as `headers=` kwarg:

```python
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
```

> Pass `headers=ws_auth_headers or None` — Playwright accepts `None` to mean "no custom headers", which matches the `none` auth mode behaviour exactly and avoids passing an empty dict.

#### 2. `_connect_selenium_cdp_grid` — CDP connect (session.py:154-158)

**File**: `framework/browser/session.py`  
**Change**: Build CDP auth headers and pass to `connect_over_cdp`. Also update the existing catch block to detect 401:

Build headers before the `try` block at line 154:
```python
cdp_auth_headers = _build_grid_auth_headers(
    runtime_env.grid_cdp_auth_mode,
    runtime_env.grid_cdp_username,
    runtime_env.grid_cdp_password,
    runtime_env.grid_cdp_token,
)
```

Pass to connect call:
```python
browser = playwright_instance.chromium.connect_over_cdp(
    cdp_endpoint,
    timeout=runtime_env.grid_connect_timeout_ms,
    headers=cdp_auth_headers or None,
)
```

In the existing `except Exception as exc` block (lines 159-173), add a 401 check before the existing re-raise:
```python
except Exception as exc:
    msg = str(exc)
    if "401" in msg or "unauthorized" in msg.lower():
        if selenium_session_id and selenium_grid_url:
            try:
                _delete_selenium_session(
                    grid_url=selenium_grid_url,
                    session_id=selenium_session_id,
                    timeout_ms=runtime_env.grid_connect_timeout_ms,
                )
            except Exception:
                pass
        raise GridAuthError(
            f"Grid CDP connection refused (401 Unauthorized). "
            f"Check grid_cdp_auth_mode, grid_cdp_username/grid_cdp_password or grid_cdp_token "
            f"in settings.py (or env vars GRID_CDP_AUTH_MODE / GRID_CDP_USERNAME / GRID_CDP_TOKEN). "
            f"Original error: {exc}"
        ) from exc
    # existing cleanup and re-raise continues below...
```

#### 3. `_create_selenium_session_for_cdp` — HTTP POST (session.py:235-243)

**File**: `framework/browser/session.py`  
**Change**: The function signature must receive auth headers. Add `ws_auth_headers: dict[str, str]` parameter and merge into the `headers` dict. Update the 401 check:

Add parameter to function signature:
```python
def _create_selenium_session_for_cdp(
    *,
    grid_url: str,
    browser_name: str,
    headless: bool,
    timeout_ms: int,
    ws_auth_headers: dict[str, str] | None = None,
) -> tuple[str, str]:
```

Merge headers at the POST call:
```python
request_headers = {"Content-Type": "application/json; charset=utf-8"}
if ws_auth_headers:
    request_headers.update(ws_auth_headers)
response = requests.post(
    f"{grid_url}/session",
    json=payload,
    headers=request_headers,
    timeout=timeout_seconds,
)
```

Upgrade the error check to raise `GridAuthError` on 401:
```python
if response.status_code == 401:
    raise GridAuthError(
        f"Selenium Grid session creation refused (401 Unauthorized). "
        f"Check grid_ws_auth_mode, grid_ws_username/grid_ws_password or grid_ws_token "
        f"in settings.py (or env vars GRID_WS_AUTH_MODE / GRID_WS_USERNAME / GRID_WS_TOKEN)."
    )
if response.status_code >= 400:
    error_details = _extract_webdriver_error_details(response)
    raise RuntimeError(f"Selenium Grid session creation failed (status={response.status_code}): {error_details}")
```

Update all callers in `_connect_selenium_cdp_grid` to pass `ws_auth_headers`:

Build WS auth headers at the top of `_connect_selenium_cdp_grid` (before the `if not cdp_endpoint:` block):
```python
ws_auth_headers = _build_grid_auth_headers(
    runtime_env.grid_ws_auth_mode,
    runtime_env.grid_ws_username,
    runtime_env.grid_ws_password,
    runtime_env.grid_ws_token,
)
```

Pass to both `_create_selenium_session_for_cdp` call sites within `_connect_selenium_cdp_grid`:
```python
selenium_session_id, cdp_endpoint = _create_selenium_session_for_cdp(
    grid_url=selenium_grid_url,
    browser_name=browser_name,
    headless=runtime_env.headless,
    timeout_ms=runtime_env.grid_connect_timeout_ms,
    ws_auth_headers=ws_auth_headers,
)
```
(Apply to both the primary call and the headless-fallback retry call at line 147.)

#### 4. `_try_get_grid_cdp_endpoint` — HTTP GET (session.py:288-292)

**File**: `framework/browser/session.py`  
**Change**: Add `ws_auth_headers: dict[str, str] | None = None` parameter and pass to `requests.get`:

```python
def _try_get_grid_cdp_endpoint(*, grid_url: str, session_id: str, ws_auth_headers: dict[str, str] | None = None) -> str:
    response = requests.get(
        f"{grid_url}/session/{session_id}/se/cdp",
        headers=ws_auth_headers or {},
        timeout=5,
    )
```

Update the call site in `_extract_cdp_endpoint_from_payload` (line 284) to pass `ws_auth_headers`. This means `_extract_cdp_endpoint_from_payload` must also accept and forward the parameter:

```python
def _extract_cdp_endpoint_from_payload(
    payload: dict[str, Any], *, grid_url: str, session_id: str, ws_auth_headers: dict[str, str] | None = None
) -> str:
    ...
    endpoint = _try_get_grid_cdp_endpoint(grid_url=grid_url, session_id=session_id, ws_auth_headers=ws_auth_headers)
```

Update the call site in `_create_selenium_session_for_cdp` (line 255):
```python
cdp_endpoint = _extract_cdp_endpoint_from_payload(
    response_payload, grid_url=grid_url, session_id=session_id, ws_auth_headers=ws_auth_headers
)
```

#### 5. `_delete_selenium_session` — HTTP DELETE (session.py:311-317)

**File**: `framework/browser/session.py`  
**Change**: Add `ws_auth_headers: dict[str, str] | None = None` parameter and pass to `requests.delete`:

```python
def _delete_selenium_session(*, grid_url: str, session_id: str, timeout_ms: int, ws_auth_headers: dict[str, str] | None = None) -> None:
    timeout_seconds = max(timeout_ms / 1000.0, 1.0)
    response = requests.delete(
        f"{grid_url}/session/{session_id}",
        headers=ws_auth_headers or {},
        timeout=timeout_seconds,
    )
```

Update all call sites in `_connect_selenium_cdp_grid` (lines 162-167 and the fallback at line 257 inside `_create_selenium_session_for_cdp`):

In `_connect_selenium_cdp_grid` except block:
```python
_delete_selenium_session(
    grid_url=selenium_grid_url,
    session_id=selenium_session_id,
    timeout_ms=runtime_env.grid_connect_timeout_ms,
    ws_auth_headers=ws_auth_headers,
)
```

In `_create_selenium_session_for_cdp` (line 257 — cleanup on missing CDP endpoint):
```python
_delete_selenium_session(grid_url=grid_url, session_id=session_id, timeout_ms=timeout_ms, ws_auth_headers=ws_auth_headers)
```

### Success Criteria

#### Automated Verification:
- [x] `make check` passes — typecheck covers the new signatures and `dict[str, str] | None` annotations
- [x] `make test-aso` passes — no regressions

#### Manual Verification:
- [ ] With `grid_ws_auth_mode = "basic"` and valid credentials set, Playwright WS connect carries `Authorization: Basic ...` header
- [ ] With `grid_ws_auth_mode = "token"` and token set, Playwright WS connect carries `Authorization: Bearer ...` header
- [ ] With `grid_cdp_auth_mode = "basic"`, CDP connect carries correct header
- [ ] HTTP probe requests (POST, GET, DELETE) carry WS auth headers
- [ ] A simulated 401 from `_create_selenium_session_for_cdp` raises `GridAuthError` with the hint message containing `GRID_WS_AUTH_MODE`
- [ ] A simulated 401-like exception from `browser_type.connect()` raises `GridAuthError` with the WS hint
- [ ] With `grid_ws_auth_mode = "none"` (default), no `Authorization` header is added (backward compatible)

---

## Phase 4: Documentation

### Overview

Update `.env.example` with 8 new stubs and update `README-DEV.md` with the new env var reference.

### Changes Required

#### 1. `.env.example` — Add 8 new stubs

**File**: `.env.example`  
**Change**: Insert after line 9 (`GRID_CONNECT_TIMEOUT_MS=30000`):

```
# Grid auth — WS endpoint (same host as GRID_WS_ENDPOINT; also used for Selenium HTTP probes)
GRID_WS_AUTH_MODE=none
GRID_WS_USERNAME=
GRID_WS_PASSWORD=
GRID_WS_TOKEN=

# Grid auth — CDP endpoint (independent auth for the final CDP WebSocket connection)
GRID_CDP_AUTH_MODE=none
GRID_CDP_USERNAME=
GRID_CDP_PASSWORD=
GRID_CDP_TOKEN=
```

#### 2. `README-DEV.md` — Grid auth env var reference

**File**: `README-DEV.md`  
**Change**: Add a subsection under the existing Grid configuration section documenting the 8 new env vars with a brief usage example for each auth mode (`none`, `basic`, `token`). Include a note that `GRID_WS_AUTH_MODE` credentials are also applied to Selenium HTTP probe requests.

### Success Criteria

#### Automated Verification:
- [x] `make check` passes (no Python changes in this phase)

#### Manual Verification:
- [x] `.env.example` contains all 8 new `GRID_WS_*` / `GRID_CDP_*` auth stubs
- [x] `README-DEV.md` documents how to configure Basic Auth and Token auth for secured Grid environments

---

## Testing Strategy

### Automated (existing suite, no regressions):
- `make test-aso` — full ASO regression suite; all tests use `IS_GRID_AVAILABLE=0` in CI so no grid connections are made, ensuring the new fields default silently to `none`/`""`.
- `make verify-discovery` — confirms collection is unaffected.
- `make check` — typecheck validates all new type annotations and parameter additions.

### Manual Testing Steps:
1. Set `grid_ws_auth_mode = "basic"`, `grid_ws_username = "user"`, `grid_ws_password = "pass"` in `settings.py`. Run with a grid that expects Basic Auth. Verify connection succeeds and `Authorization: Basic dXNlcjpwYXNz` appears in grid access log.
2. Set `grid_ws_auth_mode = "token"`, `grid_ws_token = "mytoken"`. Verify `Authorization: Bearer mytoken` header on connect.
3. Set `grid_ws_auth_mode = "basic"` with wrong credentials against a secured grid. Verify `GridAuthError` is raised with the actionable hint message.
4. Set `grid_ws_auth_mode = "none"` (default). Verify existing behaviour unchanged; no `Authorization` header sent.
5. `python -c "from framework.env import load_env; e = load_env(); r = repr(e); assert 'password' not in r.lower() or '***' not in r; print('PASS')"` — confirm secrets not in repr.
6. Verify env var override: `GRID_WS_AUTH_MODE=token GRID_WS_TOKEN=envtoken python -c "from framework.env import load_env; e = load_env(); assert e.grid_ws_auth_mode == 'token'"`.

## Performance Considerations

No performance impact. Auth headers are small strings computed once per test (at connect time). The `base64.b64encode` call is negligible.

## Migration Notes

- Fully backward compatible. All new fields default to `"none"` / `""` so existing `settings.py` files without the new fields continue to work via the `getattr(settings, ..., default)` guard in `load_env()`.
- No migration required for existing users.

## References

- Original ticket: `thoughts/tickets/feature_grid_auth.md`
- Research document: `thoughts/research/2026-05-13_grid_auth.md`
- Reference implementation (Basic Auth): `framework/integrations/jira/client.py:50-64`
- Reference implementation (Bearer): `framework/reporting/http_sender.py:57-70`
- RuntimeEnv dataclass: `framework/env.py:60-153`
- load_env() Jira pattern (getattr guard): `framework/env.py:472-498`
- Session connect functions: `framework/browser/session.py:113-180`
- HTTP probe functions: `framework/browser/session.py:204-317`
