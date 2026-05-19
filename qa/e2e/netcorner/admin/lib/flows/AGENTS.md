## Scope
- This file applies to all code under `qa/e2e/netcorner/admin/lib/flows/`.
- Flow code orchestrates reusable admin journeys over page object APIs.

## Flow Responsibilities
- Compose multi-step admin use-cases (login, context, navigation, maintenance actions).
- Keep methods intent-oriented and stable for test consumption.
- Keep technical precondition checks explicit (session/context readiness).

## Domain Split Rules
- Business assertions should remain in tests.
- Do not hide business outcomes in flow internals.
- Flow-level checks should focus on technical contract validity.

## API And Typing
- Keep full type hints for inputs and returns.
- Return typed objects/domain primitives, never raw locators.
- Keep flow methods small enough to remain auditable.

## Navigation And Stability
- Use deterministic admin navigation paths.
- Keep retries bounded and explicit.
- Do not add fallback ladders that mask contract breaks.

## Logging And Reporting
- Keep logs diagnostic and actionable.
- Avoid noisy logging that hides root cause signals.

## Legacy Touch Policy
- When touching legacy flows, migrate touched area toward explicit contracts.
- Do not increase hidden resilience or ambiguity.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/admin/lib`
