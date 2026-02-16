# Ingestion rules

## Request handling

- Authenticate token (if enabled).
- Enforce payload max size.
- Parse JSON and validate against `schema_version`.
- Reject unknown `event_type` with `400`.

## Idempotency

- `idempotency_key` is mandatory for v2.
- Duplicate key handling:
  - same payload fingerprint -> return `200`/`409 duplicate` (idempotent success),
  - different payload fingerprint -> return `409 conflict` and alert.

## Ordering

- Do not require strict ordering at ingestion time.
- Processor should tolerate `test_result` before `run_start` and reconcile later.

## Validation severity

- Hard fail (`400`): missing mandatory fields, invalid enum value, malformed time.
- Soft fail (`202 + warning`): optional fields malformed, unknown optional metadata.

## Storage model

- Raw immutable event log (append-only).
- Canonical projections:
  - `runs`,
  - `tests`,
  - `artifacts`,
  - `quality_signals`.

## Privacy and security

- Strip or hash sensitive headers.
- Truncate oversized stack traces.
- Keep allowlist of persisted header fields.
- Never store bearer tokens in event body tables.

## API response recommendations

- `200` accepted,
- `202` accepted with warnings,
- `400` contract violation,
- `401/403` auth failure,
- `409` idempotency conflict/duplicate,
- `413` payload too large,
- `500` server error.
