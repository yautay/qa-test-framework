# Tools Directory

This directory contains helper scripts used by local developers, testers, and CI.

## Structure

- `tools/windows/`
  - Windows setup and cleanup launchers/scripts.
  - `Setup_Windows.cmd`, `setup_windows.ps1`
  - `Cleanup_Windows.cmd`, `cleanup_windows.ps1`
- `tools/scenarios/`
  - Scenario catalog tooling.
  - `verify_scenarios.py`
- `tools/hooks/`
  - Local git hooks and installers.
- `tools/remote/`
  - Playwright remote/grid docker helpers.
- `tools/minio/`
  - Local MinIO docker setup for visual baselines.
- `tools/visual/`
  - Visual regression utility scripts.
  - Modular internals for baseline versioning/debug flows (entrypoint + parser/handlers/helpers).
- `tools/toc/`
  - TOC synchronization scripts.
  - `sync_test_cases.py` (pytest collect-only catalog)
  - `sync_stepapi_dump.py` (runtime StepAPI dump sync)
- `tools/dbeaver/`
  - Wizard parser and DBeaver connection export generator.
  - `export_wizard_connections.py`
- `tools/artifacts/`
  - Artifact cleanup scripts.
- `tools/opencode/`
  - OpenCode project command assets for E2E generation.
  - Command templates + registration helper script.

## Common commands

```bash
make verify-scenarios
make report-serve
make clean-artifacts
make clean-visual-baselines
make clean
make clean-artifacts-older DAYS=14
make test-api
make debug-remote-grid-up
make debug-remote-grid-down
make debug-minio-up
make debug-minio-down
python tools/opencode/register_project_commands.py
python tools/opencode/job_init.py --job-id=sample --title="Sample E2E job" --server-name=kadwa.zeta --scenario="Sample scenario"
python tools/opencode/job_analyze.py --job-id=sample --path=/ --path=/laptopy-biurowe
python tools/opencode/job_finalize_analysis.py --job-id=sample --answers-text="Captured chat answers"
```

## Notes

- Scenario tooling scripts live in `tools/scenarios/`.
- Visual tooling scripts live in `tools/visual/`.
- Visual baseline promotion/versioning runbook: `tools/visual/README.md`.
- Baseline operations in `tools/visual/baseline_ops/` are split by responsibility (copy, lifecycle, listing, scan, models) with `versioning.py` as compatibility re-export.
- Visual report server: `python -m framework.reporting.report_server` (hero page + run listing).
- Windows launchers/scripts live in `tools/windows/`.
- OpenCode setup and command catalog: `tools/opencode/README.md`.
- Versioned E2E job workspace: `work/e2e-jobs/README.md`.
