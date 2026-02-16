# AGENTS.md
Guide for autonomous coding agents working in this repository.
Project type: Python functional/UI/API test automation for NetCorner products.

## Scope and repository map
- Root: `/mnt/repos/nc-functional-tests-py`
- New framework code: `framework/`
- New tests root: `qa/`
- Legacy code snapshot: `legacy/`
- Pytest discovery config: `pytest.ini`
- Dependency/tool config: `pyproject.toml`
- Command entrypoints: `Makefile`

## Supplemental agent instructions
Checked for higher-priority editor/assistant rules:
- `.cursor/rules/`: not present
- `.cursorrules`: not present
- `.github/copilot-instructions.md`: not present
If any of these files appear later, treat them as higher priority than this file.

## Environment setup
Standard runtime setup:
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m playwright install chromium
```
Dev setup (includes lint/type/perf tooling):
```bash
python -m pip install -e .[dev]
```
Windows PowerShell setup:
```powershell
python -m pip install -e .[dev]
```

## Build/sanity/lint/typecheck commands
No compile/build artifact pipeline exists; use sanity checks.
```bash
# Lint
python -m ruff check qa framework
make lint
# Format check
python -m black --check qa framework
# Type checking
python -m mypy qa framework
make typecheck
# Security
python -m bandit -q -r qa framework
python -m pip_audit
# Discovery guard
python framework/pytest_discovery_guard.py
# Full quality gate
make check
```
`make check` notes:
- Includes lint/format/type/security/discovery + collect checks.

## Test commands (pytest)
Run from repo root.
```bash
# All tests
python -m pytest
make test

# Single suite/directory
python -m pytest qa/e2e

# Single test file
python -m pytest qa/.../test_something.py

# Single exact test (preferred dev loop)
python -m pytest qa/.../test_something.py::test_case_name

# Single test by -k (helpful for ddt-expanded names)
python -m pytest qa -k "test_case_name"

# Marker-based runs
python -m pytest -m "smoke"
python -m pytest -m "e2e and not slow"
make test-smoke

# Rerun failures
python -m pytest --lf
python -m pytest --ff
make test-last-failed
make test-failed-first

# Collection/parallel/reporting
python -m pytest --collect-only
python -m pytest -n auto
make collect
```

## Pytest discovery and markers (must follow)
- `testpaths = qa`
- `python_files = test_*.py, *_test.py, Test*.py`
- `addopts = --strict-markers`
- Markers: `e2e`, `api`, `smoke`, `slow`

## Code style and architecture guidelines
Keep changes minimal and consistent with Playwright-first architecture.
### Imports
- Prefer absolute imports like `from Lib...`, `from TestCases...`, `from TestData...`
- Keep relative imports only where already established
- Keep import ordering/grouping aligned with local file style
- Remove unused imports in touched code
### Formatting
- Use 4-space indentation
- Keep local quote style and wrapping style
- Avoid broad reformatting unrelated code
- Preserve existing docstring style in touched blocks
- Add comments only where logic is non-obvious
### Types
- Add type hints to new/edited functions when practical
- Follow local typing style (`list[str]`, `dict[str, str]`, `A | B`)
- Keep typing incremental; do not force strict typing rewrites
- Use explicit `-> None` for side-effect methods when feasible
### Naming conventions
- Test files must be `Test*.py`
- Test classes must start with `Test`
- Test methods should be `test_*`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Test data modules commonly use `data_*`
### Error handling and assertions
- Raise specific exceptions (`ValueError`, `TypeError`, `KeyError`, etc.)
- Do not introduce bare `except:` blocks
- Preserve legacy behavior unless refactor is explicitly requested
- Assertions should include actionable context (expected vs actual when possible)
### Test architecture patterns
- Prefer fixture-driven setup (`browser/context/page`) over class `setUp` orchestration.
- New Page Objects must use `BasePage(page)`.
- Existing locator classes under `legacy/` may be reused only as migration bridge.
- Prefer semantic selectors (`get_by_test_id`, `get_by_role`, `get_by_label`) in new code.
### Logging/config/secrets
- Use `framework/logger.py` (Loguru) for logger creation.
- Build deterministic artifact paths via `framework/artifacts.py`.
- Route environment values through `framework/env.py`.
- Never commit plaintext secrets, tokens, or credentials

## Agent workflow expectations
- Prefer focused edits over broad rewrites by default
- Validate with the smallest relevant test first (single test/file before full suite)
- If browser/grid execution is unavailable, run non-UI checks and report the gap
- Do not push to remote without explicit user instruction

## Big-bang Playwright branch mode
Use these rules when working on the dedicated migration branch for full Playwright rewrite (currently `refactor/playwright-bigbang-basepage`).
- Rewrite direction: prefer Playwright-native `browser/context/page` flow; avoid introducing `driver` abstractions in new code.
- Page Object pattern: use `BasePage(page)` and expose locators/actions from PO methods/properties.
- Migration bridge: existing locator classes and current PO business logic may be reused during transition.
- Legacy removal target: remove Selenium-style compatibility APIs (`_By`, `self.by`, `find_elements_by_xpath`, wrapper-only utilities).
- Planning source of truth: maintain progress in `PLAYWRIGHT_BIG_BANG_PLAN.md` with checkboxes and per-file completion percentages.
- Progress discipline: after each batch, update both phase checklist and tree checklist percentages.
- Fixture rule: one test must run in one isolated Playwright context (function scope).
- Artifact rule: persist fail artifacts under run-scoped directories and attach paths to test reporting payloads.
- Quality gates: keep `ruff`, `black`, `mypy`, `bandit`, `pip-audit`, and discovery guard in workflow.
