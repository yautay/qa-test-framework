## Scope
- This file applies to all code under `qa/e2e/netcorner/mailhog/lib/flows/`.
- Flow code orchestrates scenarios using page objects and runtime context.

## Flow Responsibilities
- Compose higher-level user journeys from stable page object APIs.
- Keep flow methods focused on use-case orchestration and typed outputs.
- Keep provider/environment branching explicit and bounded.

## Domain Split Rules
- Flows may validate technical preconditions (e.g. page opened, inbox available).
- Business assertions belong to tests; do not hide scenario-level assertions in flows.
- Do not move core business expectations from tests into flow internals.

## Timeout And Retry Policy
- Use deterministic timeout windows and explicit retry strategies.
- Keep polling/backoff behavior bounded and documented by constants.
- Do not add silent fallback ladders that mask contract failures.

## API And Typing
- Keep full type hints for input/output.
- Return domain primitives or typed objects; avoid returning raw Playwright locators.
- Keep public method names semantic (`get_*`, `count_*`, `has_*`).

## Step And Reporting
- Use `step` from `qa.e2e.netcorner.mailhog.lib.allure_decorators`.
- Keep step names stable and user-intent-oriented.

## Legacy Touch Policy
- When touching legacy flows, improve touched area toward explicit contract behavior.
- Do not add hidden resilience only to pass unstable runs.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/mailhog/lib`
