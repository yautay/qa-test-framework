# Current payload audit (runner status)

Audit based on current implementation in this repository:

- `framework/reporting_client.py`
- `qa/conftest.py`
- `qa/e2e/netcorner/conftest.py`

## What is already present

### run_start

- `run_id`
- `started_at`
- `browser`
- `headless`
- `worker_id`
- `git.commit`, `git.branch`, `git.user`, `git.email`

### test_result (E2E only)

- `run_id`
- `nodeid`
- `status` (`passed` or `failed`)
- `finished_at`
- `scenario`
- `run_start` snapshot
- `run_finish` snapshot
- `artifacts` local paths

### run_finish

- `run_id`
- `finished_at`
- `exit_status`

## Gaps versus v2 contract

- no `schema_version`
- no `event_id`
- no `event_type`
- no `idempotency_key`
- no `source.instance_id` / `source.origin`
- no full status model (`skipped`, `xfailed`, `xpassed`, `error`)
- no `attempt` and no flaky fields
- no run summary counters
- no portable artifact metadata (`uri`, `sha256`, `size_bytes`)
- no per-test reporting for API test suite

## Recommended runner changes (ordered)

1. Add envelope fields (`schema_version`, `event_id`, `event_type`, `idempotency_key`).
2. Add source identity fields (`instance_id`, `origin`, `framework_version`).
3. Extend status model and include non-call outcomes.
4. Add run summary counters to `run_finish`.
5. Add artifact metadata structure and optional storage URI.
6. Emit `test_result` for API tests as well.
7. Add dual-write mode (v1 + v2) during central migration.
