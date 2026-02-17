# Pytest Configuration Architecture Plan

## 1. Overview
- explain the repo scope (qa suites, shared framework, reporting, visual regression). 
- describe pytest `conftest.py` discovery order and how the root config cascades down through `qa/` and suite-specific directories.

## 2. CLI Options (root `conftest.py`)
- list each CLI flag (`--viewport`, `--visual-approve`, `--visual-scenario`, `--visual-viewports`, `--server-type`, `--server-name`, `--base-url`).
- describe the intent for each option (viewport presets, visual flow control, server selection/overrides).
- clarify default values and how these options are shared by all QA suites.

## 3. Runtime Environment & Reporting (`qa/conftest.py`)
- document the entry point: loading `RuntimeEnv`, building `RunArtifacts`, configuring logging/reporting client, and attaching shared state to `pytest.Config`.
- walk through each hook and helper:
  - `pytest_configure`: building `_runtime_env`, `_run_artifacts`, `_reporting_client`, and counters.
  - `pytest_sessionstart`: assembling the run start payload, deriving profile based on `markexpr`, capturing git metadata.
  - `pytest_runtest_protocol` and `pytest_runtest_teardown`: tracking timing/states, building artifact lists, emitting test-result payloads, updating counters, and registering scenarios.
  - `pytest_sessionfinish`: storing performance timings, logging regressions, sending run finish payload.
- describe helper utilities (`_resolve_run_profile`, `_build_source_context`, `_derive_test_status`, `_utc_now`) and their roles.
- explain how CLI overrides feed into `RuntimeEnv` (including `_base_url_resolver`, even if not wired yet) and where `settings_cli.base_url_override` fits.
- describe exported fixtures `runtime_env` and `run_artifacts` and how other suites rely on them.

## 4. Suite-Level Extensions
- outline the pattern for `qa/api/conftest.py`, `qa/visual/...`, `qa/e2e/...`: they should add domain fixtures (clients, page objects) that reference the shared runtime context.
- note that suite-level config files should avoid duplicating runtime/reporting logic; they just compose helpers scoped to their tests.

## 5. Suggested Improvements
- consider co-locating CLI option definitions with runtime/reporting hooks in `qa/conftest.py` for tighter grouping, unless global exposure is desirable.
- verify if `_base_url_resolver` should be invoked (e.g., from `pytest_configure`) or removed, and document how base URLs are resolved.
- ensure documentation captures how to extend reporting payloads or add new metrics (update `_run_*_payload` and `ReportingClient`).

## 6. Next Steps for Developers
- reference the files that define the recommendations (`conftest.py`, `qa/conftest.py`, etc.).
- explain how to add a new CLI option or fixture, and how to propagate it through shared runtime state.
- suggest verifying changes with focused pytest runs (e.g., `python -m pytest qa/api`).
