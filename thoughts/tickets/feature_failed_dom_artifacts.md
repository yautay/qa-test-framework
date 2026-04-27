---
type: feature
priority: high
created: 2026-04-27T00:00:00Z
status: reviewed
tags: [pytest, xdist, e2e, visual, artifacts, dom]
keywords: [failed-dom, page.content, pytest_runtest_makereport, rep_call, RunArtifacts, settings.py, xdist worker_id, retry final failure]
patterns: [failure-artifact capture, xdist-safe file naming, retry final-outcome handling, browser-fixture teardown hooks, placeholder-html fallback]
---

# FEATURE-001: DOM snapshot artifact for failed browser tests

## Description
Add automatic DOM snapshot capture as an artifact for failed browser tests so QA/DEV can quickly debug failures and use HTML context for AI-assisted analysis. For each failed test, save one rendered DOM snapshot (`.html`) under the run artifacts in `artifacts/<run_id>/failed-dom`.

## Context
Current failure artifacts (trace/screenshot/video) do not always provide enough structure-level context about the DOM state at failure time. This slows down triage and makes post-failure analysis harder. The new artifact targets faster local and CI debugging for browser-based suites.

## Requirements
Feature applies to browser-based suites only (`e2e` and `visual`). Must work in both regular pytest runs and `pytest-xdist` parallel runs.

### Functional Requirements
- Capture DOM only for failed browser tests, not for passed tests.
- Scope capture to `e2e` and `visual` suites.
- Save one `.html` artifact per failed test into `artifacts/<run_id>/failed-dom`.
- Capture rendered HTML (equivalent of Playwright `page.content()`), with no graphics requirements.
- If no active page/context is available at failure time, write a placeholder `.html` containing failure context.
- Under retries/flaky behavior, persist DOM only for final failure outcome (not intermediate failed attempts).
- Ensure unique file naming safe for `xdist` worker parallelism and nodeid collisions.
- Add the artifact to existing artifact payload flow where applicable so it is consistently discoverable.
- Add documentation describing how this mechanism works.

### Non-Functional Requirements
- Compatible with both non-xdist and xdist execution.
- Avoid filename conflicts across workers and repeated test nodeids.
- Should not introduce additional test failures when snapshot capture fails (best-effort with placeholder fallback).
- Controlled by configuration flag, default enabled in `settings.py`.

## Current State
Artifacts currently include logs/traces/screenshots/videos and selected visual outputs; there is no dedicated failed DOM HTML artifact directory or capture path. Existing failure capture logic is distributed across pytest hooks/fixtures.

## Desired State
When a browser test in `e2e` or `visual` fails, a deterministic `.html` DOM artifact is available in `artifacts/<run_id>/failed-dom`, with collision-safe naming and behavior consistent under xdist and retries.

## Research Context
Investigate current artifact and failure-hook architecture to determine the safest insertion point(s) for DOM capture and payload registration.

### Keywords to Search
- `qa/e2e/conftest.py` - Existing fail artifact capture lifecycle for browser fixtures.
- `pytest_runtest_makereport` - Failure outcome source (`rep_call`) used by teardown logic.
- `framework/artifacts.py` - Run artifact directory model (`RunArtifacts`) and subdirectory creation.
- `RunArtifacts` - Where to add `failed-dom` path cleanly.
- `settings.py` - Default-enabled config toggle location.
- `settings_cli.py` - Runtime override path for new flag if needed.
- `RuntimeEnv` - Config propagation into fixtures/hooks.
- `PYTEST_XDIST_WORKER` - Worker-aware uniqueness and metadata.
- `_artifacts_payload` - Existing test artifact transport into reporting payload.
- `rep_call` / retry plugins - Final-failure detection strategy.

### Patterns to Investigate
- Failure artifact collection pattern - Where trace/screenshot/video are captured now.
- Xdist-safe naming pattern - Existing worker-aware file naming and merge behavior.
- Hook vs fixture teardown timing - Best point to still access page/context DOM.
- Placeholder fallback pattern - How to persist useful artifacts on capture exceptions.
- Retry-aware reporting pattern - How final vs intermediate attempts are determined.
- Documentation update pattern - Where runtime artifact behavior is documented.

### Key Decisions Made
- Capture goal is fast debug and AI-assisted analysis from DOM snapshots.
- Primary users are QA and developers.
- Artifact format is `.html` containing rendered DOM only.
- Storage directory is `artifacts/<run_id>/failed-dom`.
- Scope is only browser suites: `e2e` and `visual`.
- Capture triggers only on failure.
- On missing page/context, write placeholder `.html` with error information.
- Under retries, keep only final-failure DOM artifact.
- Naming must be collision-safe under xdist.
- Feature is controlled by a config flag, default `True` in `settings.py`.
- Documentation update is in scope (describe behavior, no extra usage tutorial required).

## Success Criteria
Feature is complete when failed browser tests reliably produce unique DOM artifacts in both local and xdist runs, including fallback placeholder behavior, and documentation reflects the new artifact.

### Automated Verification
- [ ] Relevant unit/regression tests cover DOM artifact creation for failed `e2e` and `visual` tests.
- [ ] Tests validate xdist-safe naming (no collisions with `-n` execution).
- [ ] Tests validate retry behavior stores artifact only for final failure.
- [ ] Tests validate placeholder `.html` generation when page/context is unavailable.
- [ ] `make verify-discovery` passes.

### Manual Verification
- [ ] Run a failing `e2e` browser test and confirm `.html` file in `artifacts/<run_id>/failed-dom`.
- [ ] Run a failing `visual` browser test and confirm `.html` file in `artifacts/<run_id>/failed-dom`.
- [ ] Run with xdist (e.g., `-n 2+`) and confirm no filename conflicts.
- [ ] Confirm passed tests do not produce failed-dom artifacts.
- [ ] Confirm docs mention failed DOM artifact behavior and location.

## Related Information
- Existing artifact directory model: `framework/artifacts.py`.
- Existing failure/report hook pipeline: `qa/conftest.py` and suite-level conftests.
- Existing browser fail artifact handling: `qa/e2e/conftest.py`.

## Notes
- Keep ticket atomic: implement DOM-on-fail artifact capture and docs only.
- If additional enhancements emerge (report UI linking, sanitization/redaction, compression), split into follow-up tickets.
