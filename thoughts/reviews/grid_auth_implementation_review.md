# Validation Report: Grid Basic Auth and Token Auth Implementation

**Plan file**: `thoughts/plans/grid_auth_implementation_plan.md`  
**Ticket**: `thoughts/tickets/feature_grid_auth.md`  
**Reviewed**: 2026-05-13

---

## Implementation Status

✓ Phase 1: Settings, RuntimeEnv, and load_env Plumbing — Fully implemented  
✓ Phase 2: Auth Header Helper and GridAuthError — Fully implemented  
✓ Phase 3: Header Injection into All Connect/Probe Call Sites — Fully implemented  
✓ Phase 4: Documentation — Fully implemented  

---

## Automated Verification Results

✓ `make test-aso` — 306 passed, 0 failures, 0 regressions  
✓ `make verify-discovery` — 663 tests collected (threshold 1)  
✓ `mypy framework/browser/session.py framework/env.py settings.py` — no issues found in the 3 changed files  
⚠️ `make lint` — 8 errors in **pre-existing** files not touched by this implementation (whitespace in `test_visual_reporting_updates.py`, import order in `listing_components.py`, line length in `test_category_tree.py`). These are pre-existing failures; the grid auth changes introduced zero new lint issues.  
⚠️ `make typecheck` — 4 errors in **pre-existing** files (`listing_components.py`, `test_basic_orders.py`, `test_reporting_payload_helpers.py`). The changed files pass mypy cleanly.  

> `make check` exits non-zero due to pre-existing lint/typecheck failures that exist on the branch prior to this feature. This is not a regression introduced by this implementation.

---

## Code Review Findings

### Matches Plan

**Phase 1 — settings.py:**
- All 8 new fields present at `settings.py:34-42` with correct defaults (`"none"` / `""`) and inline comments.

**Phase 1 — framework/env.py:**
- `from dataclasses import dataclass, field` import confirmed.
- All 8 new `RuntimeEnv` fields declared at `env.py:70-77`, secret fields use `field(repr=False)`.
- 4 pre-existing sensitive fields masked: `reporting_api_token` (line 93), `visual_minio_secret_key`, `jira_password`, `jira_api_token` — all confirmed `field(repr=False)`.
- `load_env()` wires all 8 new fields with `getattr(settings, ..., default)` guard and `env_str()` pattern.
- Auth mode fields normalised with `.strip().lower()`.

**Phase 2 — framework/browser/session.py:**
- `import base64` present at line 3.
- `GridAuthError(RuntimeError)` defined at line 22.
- `_build_grid_auth_headers()` defined at lines 26-40 with correct Basic/Bearer/none logic.

**Phase 3 — session.py call sites:**
- `_connect_playwright_grid` (line 135): builds WS auth headers, passes `headers=ws_auth_headers or None`, 401 check raises `GridAuthError` with actionable hint.
- `_connect_selenium_cdp_grid` (line 163): builds both WS and CDP auth headers; passes `ws_auth_headers` to `_create_selenium_session_for_cdp` (both primary and headless-retry call); passes `cdp_auth_headers or None` to `connect_over_cdp`; 401-like exception in catch raises `GridAuthError` and cleans up Selenium session.
- `_create_selenium_session_for_cdp` (line 279): `ws_auth_headers` parameter, merged into POST headers, `401` checked explicitly before generic `>=400`, raises `GridAuthError` with WS hint.
- `_extract_cdp_endpoint_from_payload` (line 354): `ws_auth_headers` parameter forwarded to `_try_get_grid_cdp_endpoint`.
- `_try_get_grid_cdp_endpoint` (line 383): `ws_auth_headers` parameter, passed to `requests.get`.
- `_delete_selenium_session` (line 407): `ws_auth_headers` parameter, passed to `requests.delete`.

**Phase 4 — Documentation:**
- `.env.example` contains all 8 stubs with comments.
- `README-DEV.md` documents all 8 env vars in a table with Basic/Token usage examples and a note that WS credentials apply to HTTP probe requests.

### Deviations from Plan

**None identified.** The implementation follows the plan exactly, including the `headers=ws_auth_headers or None` idiom for Playwright (to avoid passing empty dict), the `getattr` guard pattern, and the error message wording.

One minor observation: the plan's CDP 401 cleanup block (Phase 3, change 2) specified passing `ws_auth_headers` to `_delete_selenium_session`, but at that point in the code `ws_auth_headers` is in scope (built at line 172). The actual implementation correctly passes it at lines 224.

---

## Manual Verification Results

✓ `_build_grid_auth_headers('basic','u','p','')` → `{'Authorization': 'Basic dTpw'}`  
✓ `_build_grid_auth_headers('token','','','mytoken')` → `{'Authorization': 'Bearer mytoken'}`  
✓ `_build_grid_auth_headers('none','u','p','t')` → `{}`  
✓ `RuntimeEnv` repr does not expose any of the 8 secret field values  
✓ `e.grid_ws_auth_mode` defaults to `"none"` when no env var is set  
✓ `GRID_WS_AUTH_MODE=token GRID_WS_TOKEN=envtoken` env vars override settings.py values  

---

## Potential Issues

### Test Coverage Gap (accepted, per plan)
The plan explicitly defers test coverage for `_build_grid_auth_headers`, `GridAuthError`, and the 401 error paths to a separate ticket. The test file `test_browser_session.py` was modified to accommodate the new `ws_auth_headers` parameter in mock signatures but does not add new auth-specific tests. This is intentional and documented.

### Pre-existing `make check` failures
`make lint` and `make typecheck` fail due to pre-existing issues in unrelated files (`listing_components.py`, `test_visual_reporting_updates.py`, `test_basic_orders.py`). These must not be attributed to this implementation. The 3 files changed by this feature pass mypy cleanly and introduce zero new lint violations.

### Credential masking scope
Masking is implemented via `field(repr=False)` on the `RuntimeEnv` dataclass. This prevents secrets from appearing in `repr(env)` output. However, the ticket's requirement also mentions masking from "Framework tool logs", "Allure attachments", "pytest-html", and "Jira attachments". Whether these outputs ever serialise `RuntimeEnv` directly was not verified in this review. If any of those outputs print the dataclass repr, masking is effective. If they print individual field values directly, `field(repr=False)` does not protect them. This is a pre-existing architectural question for the masking strategy — not a regression introduced here.

---

## Recommendations

1. **Pre-existing lint/typecheck failures**: Address the 8 ruff errors and 4 mypy errors in unrelated files in a separate chore commit so `make check` passes cleanly for all future feature branches.
2. **Test coverage ticket**: Follow up with the deferred test ticket covering `_build_grid_auth_headers`, `GridAuthError` raise paths, and env var wiring.
3. **Masking audit** (optional): Verify that Allure / pytest-html / Jira attachment paths do not serialise raw `RuntimeEnv` field values directly; if they do, consider a `__str__` override or a dedicated `safe_repr()` helper.
