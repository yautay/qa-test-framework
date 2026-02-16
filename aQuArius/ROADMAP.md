# aQuArius roadmap

## Phase 0 - contract and alignment
- [ ] Confirm v2 event contract.
- [ ] Confirm idempotency key strategy.
- [ ] Confirm required source identity fields.
- [ ] Publish migration timeline for runner teams.

## Phase 1 - ingestion MVP
- [ ] Build `/events` ingestion endpoint.
- [ ] Add v2 contract validation.
- [ ] Add idempotency store and duplicate handling.
- [ ] Persist raw immutable event stream.

## Phase 2 - canonical projections
- [ ] Build `runs` projection.
- [ ] Build `tests` projection.
- [ ] Build `artifacts` projection.
- [ ] Build run summary and duration projection.

## Phase 3 - analytics plugins
- [ ] Add flaky detection plugin.
- [ ] Add slow regression plugin.
- [ ] Add failure clustering plugin.
- [ ] Add visual trend analytics for `pixel_changed_ratio`, `lpips`, `dists`.
- [ ] Add threshold recommendation engine (scope: scenario+viewport+browser, no env split).
- [ ] Enforce recommendation minimum sample size: 20 runs.
- [ ] Enforce recommendation max increase guardrail: +20% per update.

## Phase 4 - policy and gates
- [ ] Add profile policies (`pr`, `nightly`, `release`).
- [ ] Add quality gate computation endpoint.
- [ ] Add release blocker reasons and audit trail.
- [ ] Add recommendation review endpoint/UI for visual thresholds.
- [ ] Add audit trail for accepted/rejected threshold changes.

## Phase 5 - observability and operations
- [ ] Add ingestion and processing metrics.
- [ ] Add plugin health dashboard.
- [ ] Add dead-letter handling for invalid events.
- [ ] Add backfill/rebuild jobs for projections.

## Phase 6 - runner migration to v2
- [ ] Deploy central support for v1 + v2.
- [ ] Upgrade runner payload writers to v2.
- [ ] Monitor parity and data completeness.
- [ ] Sunset v1 contract after freeze window.
