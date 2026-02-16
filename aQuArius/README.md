# aQuArius - central test intelligence hub

This directory contains architecture and contract documentation for the central unit
that aggregates test data from many framework instances (local testers, CI runners,
dedicated servers).

## Why this exists

The local framework should stay focused on test execution. Heavy analytics and policy
logic should run in one central system that receives events from all runners.

## Scope split

- Edge runner (this repository):
  - executes tests,
  - captures artifacts,
  - sends run/test events.
- Central hub (aQuArius, separate repository):
  - ingests and deduplicates events,
  - stores run history,
  - computes quality analytics,
  - applies release and health policies,
  - exposes dashboards and alerts.

## Document map

- `aQuArius/ARCHITECTURE.md` - target architecture and data flow
- `aQuArius/EVENT_CONTRACT_V2.md` - event payload contract (v2)
- `aQuArius/INGESTION_RULES.md` - ingestion, idempotency, deduplication rules
- `aQuArius/PLUGIN_MODEL.md` - plugin model for central analytics/policies
- `aQuArius/AGENT_GUIDELINES.md` - instructions for coding agents in central repo
- `aQuArius/ROADMAP.md` - phased implementation plan

## Current gap summary

Current reporting payloads are useful but not complete for multi-runner analytics.
Main gaps:

- no schema versioning,
- no event id/idempotency key,
- no stable runner instance identity,
- no full result status model (`skipped`, `xfailed`, `xpassed`, `error`),
- run finish has no summary counters,
- artifacts are local paths only (no portable URI/hash metadata).

## Visual threshold assumptions (AQ side)

For visual regression tuning and trend analytics:

- Threshold scope is `scenario_id + viewport + browser_family`.
- Environment (`env_name`, host) is **not** part of threshold identity.
- AQ stores both:
  - measured scores (`pixel_changed_ratio`, `lpips`, `dists`),
  - thresholds used by runner at evaluation time.
- AQ computes threshold recommendations only when sample size is at least 20 runs.
- AQ recommendation guardrail:
  - maximum one-step threshold increase is `+20%` relative to current value.
- AQ exposes recommendations as suggestions; runner/repo applies them through controlled workflow (no silent auto-overwrite).
