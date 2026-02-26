# Tools Directory

This directory contains helper scripts used by local developers, testers, and CI.

## Structure

- `tools/windows/`
  - Windows setup and cleanup launchers/scripts.
  - `Setup_Windows.cmd`, `setup_windows.ps1`
  - `Cleanup_Windows.cmd`, `cleanup_windows.ps1`
- `tools/scenarios/`
  - Scenario catalog tooling.
  - `verify_scenarios.py`, `scenario_report.py`
- `tools/reporting/`
  - Local reporting API test receiver.
  - `test_api.py`, `test_api_captures.jsonl`
- `tools/hooks/`
  - Local git hooks and installers.
- `tools/remote/`
  - Playwright remote/grid docker helpers.
- `tools/minio/`
  - Local MinIO docker setup for visual baselines.
- `tools/visual/`
  - Visual regression utility scripts.
- `tools/artifacts/`
  - Artifact cleanup scripts.

## Common commands

```bash
make verify-scenarios
make scenario-report
make visual-report-serve
make clean-artifacts
make clean-artifacts-older DAYS=14
make test-api
make remote-up
make remote-down
make minio-up
make minio-down
```

## Notes

- Scenario tooling scripts live in `tools/scenarios/`.
- Reporting helper API lives in `tools/reporting/test_api.py`.
- Visual tooling scripts live in `tools/visual/`.
- Visual report server: `tools/visual/report_server.py` (hero page + run listing).
- Windows launchers/scripts live in `tools/windows/`.
