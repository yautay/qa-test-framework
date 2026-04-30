# FEATURE-001 Failed DOM Artifacts Implementation Plan

## Overview

Implement automatic DOM snapshot artifact capture (`.html`) for failed browser tests in `e2e` and `visual`, persisted under `artifacts/<run_id>/failed-dom`, integrated into existing reporting payloads, and enabled by default via runtime config.

The implementation intentionally uses deterministic per-test filenames and overwrite semantics so retry/intermediate failures do not accumulate; only the latest failed attempt artifact remains on disk for each test nodeid.

## Current State Analysis

The framework already has a mature failure artifact pipeline for trace/screenshot/video and visual artifacts but no failed DOM artifact path.

- Artifact model has only `traces`, `screenshots`, `videos`, `logs` (`framework/artifacts.py:12`).
- E2E page fixture has failure-only screenshot capture before `page.close()` (`qa/e2e/conftest.py:266`).
- Visual page fixture currently only closes page (`qa/visual/conftest.py:315`).
- Global test-result payload assembly consumes `request.node._artifacts_payload` and maps artifact kinds (`qa/conftest.py:1641`, `qa/conftest.py:1646`).
- Unknown artifact keys are currently coerced to `other` (`qa/conftest.py:1661`).
- Filename sanitization helper exists centrally (`qa/conftest.py:1140`) but e2e currently uses ad-hoc nodeid replacement (`qa/e2e/conftest.py:193`).

## Desired End State

For every failed browser test in `qa/e2e/**` and `qa/visual/**`:
- exactly one deterministic `.html` artifact path is produced under `artifacts/<run_id>/failed-dom/`,
- capture uses rendered page DOM (`page.content()`) when possible,
- fallback writes a placeholder HTML document with failure context when page/content is unavailable,
- artifact is exposed through `_artifacts_payload` and appears in reporting `artifacts[]` with explicit kind,
- behavior remains xdist-safe and does not add new test failures.

Verification of the end state:
- failing e2e/visual tests produce `failed-dom/*.html`,
- passed tests produce no failed-dom artifact,
- repeated attempts for the same nodeid overwrite the same target file,
- reporting payload contains explicit failed-dom artifact entry (not `other`).

### Key Discoveries:
- Page teardown is the safest live-page capture window (`qa/e2e/conftest.py:266`, `qa/visual/conftest.py:315`).
- Central payload assembly should remain unchanged structurally; only map/add key (`qa/conftest.py:1646`).
- Existing worker-safe naming patterns should be reused via shared sanitizer (`qa/conftest.py:1140`).
- Current generic reporting attempt model is fixed (`attempt=1`) outside visual PMS update flow (`qa/conftest.py:1689`, `qa/visual/conftest.py:182`).

## What We're NOT Doing

- No strict retry-plugin-specific "final attempt" detection logic.
- No Allure attachment for DOM HTML in this ticket (artifact/report payload only).
- No redaction/sanitization/compression of DOM output.
- No report UI feature work (link rendering enhancements) beyond payload/docs compatibility.

## Implementation Approach

Use suite-local capture + centralized publication pattern already used by trace/screenshot/video:
1. Add canonical `failed-dom` run directory and runtime toggle.
2. In e2e/visual page teardown on failure, capture DOM before `page.close()`.
3. Write deterministic HTML filename from sanitized nodeid (`<safe_nodeid>.failed-dom.html`), overwriting existing file.
4. Add artifact key in `_artifacts_payload` (proposed key and kind: `failed_dom`).
5. Extend global `kind_map` and documentation.
6. Add focused tests in existing ASO framework test modules.

Deterministic overwrite strategy ensures only latest failed attempt is retained for a nodeid, satisfying practical final-failure retention without introducing retry-framework coupling.

## Phase 1: Artifact Model and Runtime Flag

### Overview
Create first-class directory and config plumbing for failed DOM artifacts.

### Changes Required:

#### 1. Run artifact model
**File**: `framework/artifacts.py`
**Changes**:
- Add `failed_dom: Path` field to `RunArtifacts`.
- Create `<run_root>/failed-dom` in `build_run_artifacts(...)`.

```python
@dataclass(frozen=True)
class RunArtifacts:
    ...
    failed_dom: Path

failed_dom = root / "failed-dom"
for path in (root, traces, screenshots, videos, logs, failed_dom):
    path.mkdir(parents=True, exist_ok=True)
```

#### 2. Runtime environment flag
**File**: `settings.py`
**Changes**:
- Add default-enabled setting, e.g. `failed_dom_enabled = True`.

**File**: `framework/env.py`
**Changes**:
- Add `failed_dom_enabled: bool` to `RuntimeEnv` dataclass.
- Populate from env var (e.g. `FAILED_DOM_ENABLED`) with `settings.failed_dom_enabled` fallback.

### Success Criteria:

#### Automated Verification:
- [ ] `RunArtifacts` exposes `failed_dom` and directory exists after build.
- [ ] Runtime env resolves `FAILED_DOM_ENABLED` override correctly.
- [ ] `make test-aso` passes for impacted tests.

#### Manual Verification:
- [ ] Running any test session creates `artifacts/<run_id>/failed-dom/`.
- [ ] Toggle via env (`FAILED_DOM_ENABLED=0/1`) changes behavior as expected.

---

## Phase 2: E2E and Visual DOM Capture Hooks

### Overview
Capture and persist failed DOM HTML in suite `page` teardown before browser page close.

### Changes Required:

#### 1. Shared helper(s) for safe DOM write
**File**: `qa/e2e/conftest.py` (or extracted helper module under `framework/` if preferred)
**Changes**:
- Add helper to compute deterministic filename from sanitized nodeid.
- Add best-effort write path with placeholder fallback HTML.
- Use UTF-8 output and include minimal metadata (`nodeid`, timestamp, reason/error).

```python
safe_nodeid = _sanitize_nodeid_for_filename(request.node.nodeid)
dom_path = run_artifacts.failed_dom / f"{safe_nodeid}.failed-dom.html"
```

#### 2. E2E page fixture fail path
**File**: `qa/e2e/conftest.py`
**Changes**:
- In failure branch before `page.close()` (`qa/e2e/conftest.py:266`), capture `page.content()` when `runtime_env.failed_dom_enabled`.
- On capture exception/unavailable page, write placeholder HTML.
- Add path into node payload via `request.node._screenshot_artifacts` merge path or direct `_artifacts_payload` contribution (preferred: direct payload merge discipline with existing artifact assembly).

#### 3. Visual page fixture fail path
**File**: `qa/visual/conftest.py`
**Changes**:
- Convert `page` fixture to receive `request`, `run_artifacts`, and `runtime_env`.
- On failed call (`request.node.rep_call.failed`) and `runtime_env.failed_dom_enabled`, write DOM/placeholder before `page.close()`.
- Merge/append into existing `request.node._artifacts_payload` so `framework/visual/visual_suite.py` artifacts remain preserved.

### Success Criteria:

#### Automated Verification:
- [ ] Failing e2e fixture path emits failed-dom artifact.
- [ ] Failing visual fixture path emits failed-dom artifact.
- [ ] Passed tests do not create failed-dom artifacts.
- [ ] Capture exceptions produce placeholder HTML, not fixture failure.

#### Manual Verification:
- [ ] Intentionally failing e2e test creates one HTML file in `failed-dom/`.
- [ ] Intentionally failing visual test creates one HTML file in `failed-dom/`.
- [ ] HTML content is readable and includes either rendered DOM or placeholder reason.

---

## Phase 3: Reporting Mapping and Documentation

### Overview
Make failed-dom discoverable in test-result payloads and docs.

### Changes Required:

#### 1. Artifact kind mapping
**File**: `qa/conftest.py`
**Changes**:
- Extend `kind_map` (`qa/conftest.py:1646`) with key `failed_dom` -> kind `failed_dom`.
- Ensure emitted artifacts do not fall back to `other` for this key.

```python
kind_map = {
    ...,
    "failed_dom": "failed_dom",
}
```

#### 2. Artifact layout docs
**File**: `docs/ARTIFACTS.md`
**Changes**:
- Add `artifacts/<run_id>/failed-dom/` to directory layout and writing responsibilities.
- Clarify deterministic naming/overwrite behavior for retries.

#### 3. Reporting integration docs
**File**: `docs/REPORTING_HTTP_INTEGRATION.md`
**Changes**:
- Update test-result artifact docs to include failed-dom kind in `artifacts` metadata list.
- Clarify this is path+metadata in JSON payload (not multipart screenshot upload channel).

### Success Criteria:

#### Automated Verification:
- [ ] Reporting helper tests assert failed-dom kind is preserved.
- [ ] Lint/docs checks in `make check` stages remain green.

#### Manual Verification:
- [ ] Sample emitted `test_result` payload contains `{"kind": "failed_dom", ...}`.
- [ ] Docs clearly describe storage path and behavior.

---

## Phase 4: Test Coverage and Regression Safety

### Overview
Add targeted tests for artifact creation, naming, placeholder fallback, and payload mapping.

### Changes Required:

#### 1. Artifact model tests
**File**: `qa/aso/framework/test_sessionfinish_collect_only.py` (or new dedicated test module)
**Changes**:
- Assert `build_run_artifacts` creates `failed-dom` directory.

#### 2. Reporting helper tests
**File**: `qa/aso/framework/test_reporting_payload_helpers.py`
**Changes**:
- Add test for `_artifact_entry("failed_dom", path)` with real HTML file.
- Add missing-path test for failed-dom.

#### 3. Visual update merge safety tests
**File**: `qa/aso/framework/visual/test_visual_reporting_updates.py`
**Changes**:
- Ensure attempt-2 visual updates preserve unrelated artifacts including `failed_dom` from base payload.

#### 4. Xdist finalize tests
**File**: `qa/aso/framework/plugins/test_xdist_report_finalize.py`
**Changes**:
- Add case where worker payload contains `failed_dom` and verify it survives update merge.

### Success Criteria:

#### Automated Verification:
- [ ] `make test-aso` passes with new/updated tests.
- [ ] `make verify-discovery` passes.
- [ ] No regressions in existing reporting update tests.

#### Manual Verification:
- [ ] Run failing tests with `-n 2` and confirm no failed-dom filename collisions.
- [ ] Re-run same failing test; confirm same file path is overwritten (latest artifact retained).

---

## Testing Strategy

### Unit Tests:
- Run artifact directory creation includes `failed-dom`.
- `_artifact_entry` computes availability/hash/size for failed-dom HTML paths.
- Placeholder generation path writes valid HTML and includes context markers.

### Integration Tests:
- E2E fail path includes `failed_dom` in payload artifact list.
- Visual attempt-2 postprocess updates preserve `failed_dom` artifact from attempt-1 payload.
- Xdist worker payload merge keeps failed-dom entry stable.

### Manual Testing Steps:
1. Trigger a deterministic failing e2e browser test; verify `artifacts/<run_id>/failed-dom/<safe_nodeid>.failed-dom.html` exists.
2. Trigger a deterministic failing visual browser test; verify same behavior.
3. Run with xdist (`pytest -n 2 ...`) and confirm no collisions across workers.
4. Force DOM capture exception (closed page) and verify placeholder HTML is written.
5. Re-run same failing nodeid multiple times and verify single overwritten file path.

## Performance Considerations

- `page.content()` can be large; this is only on failed tests and best-effort.
- Deterministic overwrite avoids unbounded growth from retries/re-runs of same test nodeid.
- No additional network calls; only local file write + existing payload metadata computation.

## Migration Notes

- No data migration required.
- Historical runs without `failed-dom/` remain valid.
- Consumers treating unknown kinds as `other` remain backward compatible even before mapping updates deploy.

## References

- Original ticket: `thoughts/tickets/feature_failed_dom_artifacts.md`
- Related research: `thoughts/research/2026-04-27_failed_dom_artifacts.md`
- Similar implementation points:
  - `qa/e2e/conftest.py:266`
  - `qa/visual/conftest.py:315`
  - `qa/conftest.py:1646`
  - `framework/artifacts.py:12`
