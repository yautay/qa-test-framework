---
date: 2026-04-27T12:05:18+02:00
git_commit: 313cb653489101040176758a1d818fee9b60728d
branch: feature/NN-23913-e2e-nuxt-smoke-tests
repository: qa-test-netquarner
topic: "FEATURE-001: DOM snapshot artifact for failed browser tests"
tags: [research, codebase, artifacts, pytest, e2e, visual, xdist, reporting]
last_updated: 2026-04-27
---

## Ticket Synopsis
The ticket requests a new failure artifact for browser suites: one rendered DOM snapshot (`.html`) per failed test, stored at `artifacts/<run_id>/failed-dom`, with xdist-safe naming, placeholder fallback when page/context is unavailable, retry-aware final-failure behavior, and integration into the existing artifact payload/reporting flow.

## Summary
The codebase already has a mature failure artifact pipeline for `e2e` and `visual`, but no `failed-dom` path or artifact kind yet. The safest capture timing is in suite `page` fixture teardown before `page.close()` (`qa/e2e/conftest.py:266`, `qa/visual/conftest.py:315`), then forwarding path via `request.node._artifacts_payload` into global payload assembly (`qa/conftest.py:1641`).

The best integration points are:
- artifact directory model (`framework/artifacts.py:11`, `framework/artifacts.py:56`),
- runtime toggle plumbing (`settings.py:10`, `framework/env.py:60`, `framework/env.py:221`),
- reporting kind map (`qa/conftest.py:1646`),
- docs (`docs/ARTIFACTS.md:5`, `docs/REPORTING_HTTP_INTEGRATION.md:140`).

Main risk: generic retry/final-attempt semantics are not fully implemented for test failures (normal payloads are emitted with `attempt=1` in `qa/conftest.py:1689`), so final-failure-only DOM persistence needs explicit design.

## Detailed Findings

### Failure Artifact Lifecycle (E2E + Visual)
- `rep_*` reports are cached on items in `pytest_runtest_makereport` (`qa/e2e/conftest.py:147`, `qa/conftest.py:1522`), enabling `rep_call.failed` checks during teardown.
- E2E currently captures trace/video/screenshot in fixture teardown and stores into node payload (`qa/e2e/conftest.py:192`, `qa/e2e/conftest.py:205`, `qa/e2e/conftest.py:220`, `qa/e2e/conftest.py:320`, `qa/e2e/conftest.py:246`).
- Visual suite stores visual artifact paths via `request.node._artifacts_payload` in `framework/visual/visual_suite.py:196`, but visual `page` fixture teardown currently just closes the page (`qa/visual/conftest.py:315`).
- Global reporting hook consumes `_artifacts_payload` and converts to artifact entries (`qa/conftest.py:1641`, `qa/conftest.py:1658`, `qa/conftest.py:1699`).

### RunArtifacts Model and Directory Ownership
- `RunArtifacts` currently exposes `traces`, `screenshots`, `videos`, `logs` only (`framework/artifacts.py:11`).
- Directories are eagerly created in `build_run_artifacts` (`framework/artifacts.py:56`, `framework/artifacts.py:61`).
- `docs/ARTIFACTS.md` documents run layout and is the canonical place to add `failed-dom` (`docs/ARTIFACTS.md:5`, `docs/ARTIFACTS.md:30`).

### Xdist Safety and Naming Patterns
- Shared run identity is propagated from controller to workers (`qa/conftest.py:71`, `qa/conftest.py:1473`), ensuring one `artifacts/<run_id>` root.
- Worker-scoped files use `workers/<worker_id>/...` pattern (`qa/conftest.py:1136`, `qa/conftest.py:1146`, `qa/visual/conftest.py:39`).
- Filename sanitization helper exists (`qa/conftest.py:1140`) and is stronger than ad-hoc e2e replacements (`qa/e2e/conftest.py:193`).
- Atomic temp-write/replace is used for robustness (`qa/conftest.py:620`, `qa/conftest.py:885`).

### Retry/Final-Failure Semantics
- Base test-result payload emits `attempt=1`, `is_flaky=False` (`qa/conftest.py:1689`, `qa/conftest.py:1690`), and quality counters default retry/flaky to zero (`qa/conftest.py:1573`).
- Attempt `2` exists for visual PMS postprocess updates, not generic test retries (`qa/visual/conftest.py:182`, `framework/plugins/xdist_report_finalize.py:472`).
- Ticket requirement "store only final failure under retries" is not directly satisfied by existing generic flow and needs explicit final-outcome gating logic.

### Configuration Flag Propagation
- Runtime defaults live in `settings.py` (example toggles in `settings.py:10`).
- Env/system/.env precedence is implemented by `load_env` helpers in `framework/env.py:159` and documented in `docs/REPORTING_HTTP_INTEGRATION.md:180`.
- `RuntimeEnv` schema is central (`framework/env.py:60`), and values are constructed in `load_env` return block (`framework/env.py:221`).
- Runtime is injected at pytest startup (`qa/conftest.py:1379`, `qa/conftest.py:1402`) and consumed via fixtures in e2e/visual hooks (`qa/e2e/conftest.py:162`, `qa/visual/conftest.py:283`).

### Reporting Payload Integration
- Artifact entry schema is centralized in `_artifact_entry` (`qa/conftest.py:1105`) with `kind/path/sha256/size/available`.
- Artifact key-to-kind mapping is explicit in `kind_map` (`qa/conftest.py:1646`); unknown keys become `other` (`qa/conftest.py:1661`).
- Reporting contract doc currently describes artifacts as trace/video/screenshot (`docs/REPORTING_HTTP_INTEGRATION.md:149`), so failed-dom kind must be documented there.

## Code References
- `qa/e2e/conftest.py:266` - Failure-gated `page` teardown, safest point to call `page.content()` before close.
- `qa/e2e/conftest.py:192` - Context teardown artifact assembly and `_artifacts_payload` publication.
- `qa/visual/conftest.py:315` - Visual page fixture teardown currently closes page without fail-artifact capture.
- `framework/visual/visual_suite.py:196` - Visual artifacts attached to `request.node._artifacts_payload`.
- `qa/conftest.py:1641` - Global teardown reads `_artifacts_payload` for report payload assembly.
- `qa/conftest.py:1646` - Artifact `kind_map` where new failed-dom kind should be registered.
- `qa/conftest.py:1136` - Worker-scoped artifact file path pattern (`workers/<worker_id>/...`).
- `qa/conftest.py:1140` - Shared nodeid filename sanitizer for collision-safe naming.
- `framework/artifacts.py:11` - `RunArtifacts` dataclass (no `failed-dom` path yet).
- `framework/artifacts.py:56` - Core subdirectory creation for run artifacts.
- `framework/env.py:60` - `RuntimeEnv` dataclass for flag propagation.
- `framework/env.py:221` - Central `RuntimeEnv(...)` construction from env/defaults.
- `settings.py:10` - Runtime defaults section where new feature toggle should default to enabled.
- `docs/ARTIFACTS.md:5` - Artifact directory layout docs to update with `failed-dom`.
- `docs/REPORTING_HTTP_INTEGRATION.md:140` - Test-result artifact payload documentation section.

## Architecture Insights
- Artifact production is suite-local (`qa/e2e`, `framework/visual`) but artifact publication is centralized in `qa/conftest.py`; adding failed-dom should preserve this split.
- Existing patterns strongly favor best-effort artifact capture (warning/fallback, no new test failure) and should be reused for DOM capture exceptions.
- Xdist safety in this repo relies on shared run root + worker-specific files + sanitized nodeids; failed-dom naming should align with the same primitives.
- Visual postprocess updates preserve non-visual artifacts when emitting `attempt=2`; failed-dom entries should remain stable across those updates.

## Historical Context (from thoughts/)
- `thoughts/tickets/feature_failed_dom_artifacts.md` - Only relevant thoughts document found; it defines requirements, constraints, and acceptance criteria for failed-dom behavior, including xdist/retry/fallback and default-enabled config toggle.

## Related Research
- No existing documents found under `thoughts/shared/research/`.
- No prior documents found under `thoughts/research/` before this study.

## Open Questions
- What mechanism will define "final failure" under retries for non-visual tests, given current generic payload emission is `attempt=1` only?
- Should failed-dom artifacts be staged under worker directories and published to `failed-dom/` only for final failures, or written directly with collision-proof names?
- What exact reporting artifact kind name should be used (`failed_dom`, `dom_html`, etc.) to stay consistent with downstream consumers?
- Should failed-dom be attached to Allure in e2e (parallel to screenshots/traces/videos), or remain only in run artifacts/report payload?
