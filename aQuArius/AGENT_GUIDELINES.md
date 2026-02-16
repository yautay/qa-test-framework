# Agent guidelines for central aQuArius repository

Use this document for coding agents that work in the separate central repo.

## Priorities

1. Data correctness and idempotency.
2. Backward compatibility for ingestion contracts.
3. Operational visibility (health, metrics, warnings).
4. Small, reversible migrations.

## Rules

- Treat ingestion contract as a public API.
- Never break existing payload versions without migration path.
- Keep raw event storage immutable.
- Make processors idempotent.
- Add tests for every new field/enum in the contract.
- Separate core ingestion from plugins.

## Required test coverage

- schema validation tests,
- idempotency duplicate tests,
- out-of-order event reconciliation tests,
- plugin failure isolation tests,
- policy computation tests.

## Visual threshold recommendation policy

- Use threshold scope key: `scenario_id + viewport + browser_family`.
- Do not include environment in threshold identity.
- Generate recommendations only when sample size >= 20 runs.
- Cap single-step recommended increase to +20% relative to current threshold.

## Operational checks

- expose ingestion lag,
- expose duplicate rate,
- expose invalid payload count,
- expose per-plugin health.

## Migration discipline

- introduce new fields as optional first,
- release writer then reader,
- only later mark fields as required.

## Security discipline

- redact secrets in logs,
- never persist raw auth tokens,
- enforce strict payload size limits,
- store only necessary PII.
