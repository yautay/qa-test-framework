# aQuArius architecture

## Target model

Many runner instances send events to one central ingestion API.

Event producers:

- local developer runs,
- local tester runs,
- CI runs,
- dedicated server runs.

Central aQuArius responsibilities:

- validate and deduplicate events,
- persist canonical run/test/artifact data,
- compute quality and stability metrics,
- provide query APIs and dashboards,
- trigger alerts and policy decisions.

## High-level flow

1. Runner emits `run_start`.
2. Runner emits `test_result` for each test case.
3. Runner emits `run_finish`.
4. aQuArius stores canonical records and computes derived metrics.

Optional flow:

- Runner (or helper) uploads artifacts to object storage,
- Runner emits `artifact_uploaded` with stable URI/hash,
- aQuArius links artifact metadata to test results.

## Logical components in central repo

- `ingestion-api`
  - accepts events,
  - validates schema version,
  - checks idempotency.
- `event-store`
  - immutable raw event log,
  - canonical relational projection.
- `processors`
  - enrichment,
  - flaky detection,
  - trend aggregation,
  - policy checks.
- `query-api`
  - run-level and test-level analytics,
  - quality gate endpoints.
- `scheduler`
  - periodic backfills,
  - nightly aggregates,
  - alert batch jobs.

## Reliability requirements

- at-least-once ingestion,
- idempotent processing by `idempotency_key`,
- forward compatible contract (`schema_version`),
- degraded mode when optional plugins fail (warning, not data loss).

## Security and governance

- token auth for runner clients,
- optional per-project token scopes,
- strict input size limits,
- PII-safe payload policy (no customer secrets in error stacks/artifacts).
