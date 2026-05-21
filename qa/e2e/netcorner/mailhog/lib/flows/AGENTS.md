## Scope
- This file applies to all code under `qa/e2e/netcorner/mailhog/lib/flows/`.
- Flow code orchestrates scenarios using page objects and runtime context (Playwright browser).
- For HTTP-only mailbox queries (counting, searching by text) use `MailhogApiClient` from `api/`, not flows.

## Flow Responsibilities
- Compose higher-level user journeys from stable page object APIs.
- Keep flow methods focused on use-case orchestration and typed outputs.
- Keep provider/environment branching explicit and bounded.

## Domain Split Rules
- Flows may validate technical preconditions (e.g. page opened, inbox available).
- Business assertions belong to tests; do not hide scenario-level assertions in flows.
- Do not move core business expectations from tests into flow internals.

## Polling Contract
- Use `framework.polling.poll_until` for any retry loop over UI or backend state.
- Do **not** write inline `while + time.sleep` or manual `for _ in range(n)` polling loops.
- Playwright UI readiness (waiting for a message row to appear) uses the backoff loop in `__open_message` / `__count_messages` — keep these using `page.wait_for_timeout`, not `time.sleep`.
- Backend/HTTP polling (waiting for mail to arrive via API) belongs in `MailhogApiClient.wait_for_mails_containing_text` using `HttpPoller`.

## API And Typing
- Keep full type hints for input/output.
- Return domain primitives or typed objects; avoid returning raw Playwright locators.
- Keep public method names semantic (`get_*`, `count_*`, `has_*`, `wait_for_*`).

## Step And Reporting
- Use `step` from `qa.e2e.netcorner.mailhog.lib.allure_decorators`.
- Keep step names stable and user-intent-oriented.

## Legacy Touch Policy
- When touching legacy flows, improve touched area toward explicit contract behavior.
- Do not add hidden resilience only to pass unstable runs.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/mailhog/lib`

## Timeout Constants
- Import timeout constants from `qa.e2e.netcorner.mailhog.lib.timeouts` (re-export of `framework/timeouts.py`).
- Do **not** use raw integer literals for `timeout=` arguments; always reference a named constant.
- Common constants: `QUICK_PROBE_MS`, `ELEMENT_VISIBLE_MS`, `UI_ACTION_MS`, `SLOW_OPERATION_MS`, `HTTP_REQUEST_TIMEOUT_S`.
- See root `AGENTS.md` for the full tier table and exception list.
