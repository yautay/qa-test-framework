---
type: feature
priority: medium
created: 2026-05-13T00:00:00Z
created_by: OpenCode
status: implemented
tags: [grid, auth, playwright, selenium, settings, browser-session]
keywords: [grid_ws_endpoint, grid_cdp_endpoint, grid_auth_mode, Basic Auth, Bearer token, Authorization header, browser connect, RuntimeEnv, env_str, open_browser_session]
patterns: [Authorization header injection, env var override, settings defaults, credential masking, error handling 401]
---

# FEATURE-001: Grid Basic Auth and Token Auth for WS and CDP connections

## Description
Add authentication support for connections to WS Grid (Docker Playwright and Selenium Grid). Both the WebSocket endpoint (`grid_ws_endpoint`) and the CDP endpoint (`grid_cdp_endpoint`) should support three auth modes: `none` (default, backward compatible), `basic` (username + password via `Authorization: Basic` header), and `token` (bearer token via `Authorization: Bearer` header). Credentials are stored in `settings.py` as new fields, can be overridden by environment variables (env vars take priority), and must be masked in all logs and reports.

## Context
The framework currently connects to Selenium Grid / Docker Playwright Grid without any authentication. As grid deployments gain access control, the framework needs to pass credentials at connect time. The feature was not previously needed but is now required to support secured grid environments.

The existing `jira_auth_mode` pattern (in `settings.py` / `framework/integrations/jira/client.py`) serves as a reference model. Similarly, `framework/reporting/http_sender.py` demonstrates `Authorization: Bearer` header injection.

## Requirements

### Functional Requirements

#### Settings (`settings.py`)
- Add the following fields under the `# Grid` section:
  ```
  grid_ws_auth_mode = "none"       # none | basic | token
  grid_ws_username = ""
  grid_ws_password = ""
  grid_ws_token = ""

  grid_cdp_auth_mode = "none"      # none | basic | token
  grid_cdp_username = ""
  grid_cdp_password = ""
  grid_cdp_token = ""
  ```
- Default `auth_mode` is `"none"` for backward compatibility.
- WS and CDP have independent auth configurations.

#### Environment Variable Overrides (priority over `settings.py`)
- Naming convention (uppercase, `GRID_` prefix):
  ```
  GRID_WS_AUTH_MODE
  GRID_WS_USERNAME
  GRID_WS_PASSWORD
  GRID_WS_TOKEN

  GRID_CDP_AUTH_MODE
  GRID_CDP_USERNAME
  GRID_CDP_PASSWORD
  GRID_CDP_TOKEN
  ```
- Loaded via `framework/env.py` using the existing `env_str(...)` helper pattern.
- Env vars override `settings.py` values (same as existing `GRID_WS_ENDPOINT` / `GRID_CDP_ENDPOINT` pattern).

#### `framework/env.py` - RuntimeEnv extension
- Expose all new fields in `RuntimeEnv` (frozen dataclass / namedtuple, whatever pattern exists).
- Read from env vars with fallback to `settings.py` defaults.

#### `framework/browser/session.py` - Auth header injection
- For WS connect (Playwright `browser_type.connect(...)`):
  - If `grid_ws_auth_mode == "basic"`: inject `Authorization: Basic <base64(user:pass)>` header.
  - If `grid_ws_auth_mode == "token"`: inject `Authorization: Bearer <token>` header.
  - If `grid_ws_auth_mode == "none"`: no Authorization header (current behavior).
- For CDP connect (Playwright `playwright_instance.chromium.connect_over_cdp(...)`):
  - Apply analogous logic using `grid_cdp_*` fields.
- For HTTP probing requests to Selenium Grid (`requests.get/post/delete`) used to discover `se:cdp` endpoint:
  - Apply WS auth headers to these HTTP probe requests as well (same credentials, since they target the same Grid host).
- On connect failure with a `401`-like error, raise a clear exception with a hint message, e.g.:
  ```
  GridAuthError: Grid connection refused (401). Check grid_ws_auth_mode, grid_ws_username/grid_ws_password or grid_ws_token in settings.py (or env vars GRID_WS_USERNAME / GRID_WS_TOKEN).
  ```
- Error is scoped to the individual test (not fail-fast for the entire session).

#### Credential Masking
- `grid_ws_password`, `grid_ws_token`, `grid_cdp_password`, `grid_cdp_token` must NEVER appear in:
  - Framework tool logs (`tools/logs/`)
  - Pytest output / console
  - Allure report attachments
  - pytest-html report
  - Jira attachments
- Masking strategy: replace value with `***` wherever RuntimeEnv or settings values are serialized/logged.
- Reference existing masking if any exists (check `framework/env.py` repr / `__str__`).

#### Documentation
- Add comments for all new fields in `settings.py` (inline, same style as existing fields).
- Update `README-DEV.md` and/or `tools/remote/README.md` with new env var names and example usage.
- Optionally update `.env.example` with new `GRID_*` env var stubs.

### Non-Functional Requirements
- **Backward compatibility**: default `auth_mode = "none"` ensures zero impact on existing configurations.
- **No new dependencies**: use Python stdlib `base64` for Basic Auth encoding; no new pip packages.
- **Credential scope**: credentials are passed only at connect time, not stored beyond `RuntimeEnv` lifetime.
- **Test scope exclusion**: no changes to existing unit/integration tests; no new tests in this ticket.

## Current State
- `settings.py` has `grid_ws_endpoint`, `grid_cdp_endpoint`, `grid_provider`, `grid_connect_timeout_ms` - no auth fields.
- `framework/env.py` reads `GRID_WS_ENDPOINT` / `GRID_CDP_ENDPOINT` / `GRID_PROVIDER` via `env_str(...)`.
- `framework/browser/session.py` connects with no Authorization headers.
- HTTP probe requests in `session.py` use only `Content-Type` header.

## Desired State
- `settings.py` has 8 new grid auth fields (4 for WS, 4 for CDP).
- `framework/env.py` reads 8 new `GRID_*` env vars with fallback to `settings.py`.
- `RuntimeEnv` exposes all new fields, with sensitive fields masked in repr/logs.
- `framework/browser/session.py` injects `Authorization` header for WS connect, CDP connect, and HTTP probe requests based on configured auth mode.
- Clear `GridAuthError` raised on 401 with actionable hint.
- Documentation updated.

## Research Context

### Keywords to Search
- `grid_ws_endpoint` - existing field to find all consumers and the env.py mapping pattern
- `env_str` - helper used in `framework/env.py` to read env vars; pattern to replicate for new fields
- `open_browser_session` - entry point in `framework/browser/session.py` where connect logic lives
- `browser_type.connect` - Playwright WS connect call; find where to inject headers
- `connect_over_cdp` - Playwright CDP connect call; find where to inject headers
- `requests.post` / `requests.get` - HTTP Grid probe calls in `session.py`; find where to inject headers
- `jira_auth_mode` - existing auth mode pattern in settings + client to model after
- `Authorization` - existing header injection examples (http_sender.py, jira/client.py)
- `RuntimeEnv` - frozen env dataclass; find how new fields must be declared
- `__repr__` / `__str__` of RuntimeEnv - for credential masking implementation
- `GRID_WS_ENDPOINT` in `.env.example` - to find where to add new env var stubs

### Patterns to Investigate
- `env_str("GRID_WS_ENDPOINT", ...)` in `framework/env.py` - exact pattern to replicate x8
- `Authorization: Bearer` in `framework/reporting/http_sender.py` - token header injection pattern
- `Authorization: Basic` in `framework/integrations/jira/client.py` - basic auth header pattern
- `base64.b64encode` usage (if any) - for constructing Basic Auth value
- RuntimeEnv field declaration + masking pattern - check if `__repr__` redacts secrets already
- Error handling in `session.py` connect paths - where to catch and re-raise as `GridAuthError`

### Key Decisions Made
- **Auth fields in `settings.py` only** (not in `settings_cli.py`) - per user decision
- **Env vars override settings.py** - same priority model as existing GRID_* vars
- **Separate auth config for WS and CDP** - `grid_ws_auth_mode` and `grid_cdp_auth_mode` are independent
- **Headers injected at connect time only** - no health-check or pre-validation
- **Error scope: per-test** - 401 fails the individual test, not the whole session
- **Masking scope: all outputs** - logs, Allure, pytest-html, Jira
- **No new pip dependencies** - use stdlib `base64`
- **No new tests in this ticket** - test coverage is a separate ticket
- **Naming convention for env vars**: `GRID_WS_*` / `GRID_CDP_*` prefix pattern

## Success Criteria

### Automated Verification
- [ ] `make check` passes with no regressions
- [ ] `make verify-discovery` passes (collection unaffected)
- [ ] `make test-aso` passes (existing ASO suite unaffected)

### Manual Verification
- [ ] `settings.py` contains all 8 new `grid_ws_*` / `grid_cdp_*` auth fields with `"none"` defaults
- [ ] `framework/env.py` maps 8 new `GRID_WS_*` / `GRID_CDP_*` env vars into `RuntimeEnv`
- [ ] `RuntimeEnv` repr/str does not expose password or token values
- [ ] `framework/browser/session.py` passes `Authorization: Basic ...` header when `grid_ws_auth_mode = "basic"`
- [ ] `framework/browser/session.py` passes `Authorization: Bearer ...` header when `grid_ws_auth_mode = "token"`
- [ ] Same for CDP connect path
- [ ] HTTP probe requests to Grid also carry auth headers
- [ ] 401 response raises `GridAuthError` with hint referencing correct settings keys and env var names
- [ ] Credentials do not appear in tool logs, Allure, pytest-html, or Jira attachments
- [ ] `README-DEV.md` or `tools/remote/README.md` documents new env vars
- [ ] `.env.example` updated with new `GRID_*` stubs

## Related Information
- `settings.py:28-32` - current Grid section
- `framework/env.py` - `env_str` pattern and `RuntimeEnv` construction
- `framework/browser/session.py` - `open_browser_session`, `_connect_playwright_grid`, `_connect_selenium_cdp_grid`, `_connect_auto_grid`
- `framework/integrations/jira/client.py` - Basic Auth header reference
- `framework/reporting/http_sender.py` - Bearer token header reference
- `.env.example` - env var stub reference

## Notes
- Verify whether Playwright's `browser_type.connect()` accepts a `headers` kwarg directly or requires it via `ConnectOptions`. Check Playwright Python API docs.
- Verify whether `connect_over_cdp()` accepts custom headers - Playwright Python may not support this natively; if not, research alternative (e.g., modifying the WebSocket URL to embed credentials, or using a proxy).
- Check if `RuntimeEnv` is a dataclass, namedtuple, or plain object - this affects how masking is implemented.
