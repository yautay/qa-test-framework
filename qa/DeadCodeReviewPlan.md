# Dead Code Review Plan

## 1. Scope
- focus on Pytest configuration layers, starting with shared `qa/conftest.py`, then per-suite `conftest.py` modules.
- identify helpers, fixtures, or hooks that are defined but never referenced, especially those related to runtime/env configuration.

## 2. Immediate findings
- `_base_url_resolver` in `qa/conftest.py` (lines 91‑115) is defined but never called. Consider either invoking it from `pytest_configure` (so CLI/server overrides take effect) or removing it, and note its intended behavior when documenting fixtures.

## 3. Search strategy
1. For each `conftest.py`, run `rg "def [A-Za-z_]+\(" qa -n` to list defined functions/fixtures, then search for each name to ensure there are call sites. Focus on helper functions that look like dead hooks.
2. Check `qa/framework`, `qa/api`, `qa/visual`, and `qa/e2e` directories for fixtures that may not be consumed elsewhere—look for unused markers or helpers in `conftest.py` and page objects.
3. Use `ruff`/`python -m pytest --collect-only` to surface unused imports or dead hooks flagged by linting.

## 4. Verification guidance
- After identifying suspected dead code, confirm via search (`rg "name"`) that only the definition exists (no imports/calls). Include rationale in the final review doc.
- If removing code, rerun targeted tests/linting to ensure no regressions; mention this as a follow-up in the document.

## 5. Documentation next steps
- Update the plan with each dead-code spot discovered, describing why it’s unused and whether it should be removed or reconnected.
- Keep the list ordered by impact: shared hooks first (like `_base_url_resolver`), then suite-specific utilities.
