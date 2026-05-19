# Fixtures Guide

This project uses pytest fixtures for runtime setup, Playwright lifecycle, API clients, and technical ASO checks.

## How to list available fixtures

```bash
python -m pytest qa --fixtures -q
```

This command prints fixture names, source file, scope, and fixture docstring.

## How to see fixtures used by tests

```bash
python -m pytest qa --fixtures-per-test -q
```

To inspect one concrete test:

```bash
python -m pytest qa/e2e/netcorner/nuxt/pl/tests/test_orders_smoke.py::test_order_delivery --fixtures-per-test -q
```

## How to preview setup flow (without running browser actions)

```bash
python -m pytest qa/e2e/netcorner/nuxt/pl/tests/test_orders_smoke.py::test_order_delivery --setup-plan -q
```

## How fixtures are documented

- Every project fixture should include a short docstring.
- Pytest shows that docstring in `--fixtures` output.
- Keep docstrings practical: what fixture provides, scope, and key side effects.

## Current project fixture groups

- `qa/conftest.py`: run config + artifacts (`runtime_env`, `run_artifacts`)
- `qa/e2e/netcorner/conftest.py`: Playwright lifecycle (`playwright_instance`, `browser`, `context`, `page`)
- `qa/api/conftest.py`: API client (`api_client`)
- `qa/aso/conftest.py`: technical suite fixture (`aso`)

## Marker matrix (marker -> tests)

Generate a fresh marker-to-test matrix:

```bash
.venv/bin/python tools/pytest/generate_marker_matrix.py
```

Output file:

- `docs/MARKER_TESTS_MATRIX.md`

When to update:

- after adding/removing tests,
- after changing `pytestmark` / `@pytest.mark.*`,
- after introducing new marker names in `pytest.ini`.
