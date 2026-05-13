## Scope
- This file applies to `qa/e2e/netcorner/nuxt/pl/lib/test_data/` and all nested folders.
- Keep this layer focused on test input contracts and scenario definitions used by pytest parametrization.

## Structure And Ownership
- `*_data_models.py`: data contracts only (`dataclass`, `Enum`, type aliases).
- `*_generators.py`: builders, scenario generators, and composable fixture-like factories.
- Keep tests free of inline complex case lists when equivalent generators exist in this layer.

## Parametrization Contract
- Model parametrized cases as immutable case objects with:
  - `case_id: str`
  - `factory: Callable[[], <DataModel>]` for mutable runtime data creation.
- In tests, always use:
  - `@pytest.mark.parametrize("...", <case_generator>(), ids=lambda case: case.case_id)`
- `case_id` format should be stable and descriptive: `<locale>_<feature>_<variant>`.

## Generator And Builder Rules
- Builder methods (`with_*`) only update builder state and return `self`.
- `build()` must be side-effect free and return a new data object.
- Keep defaults deterministic for business flow selection; use explicit case variants for random behavior.
- Use randomness only for uniqueness-sensitive fields (email, password, identifiers) to avoid flaky collisions.
- Prefer explicit semantic methods (`with_required_terms`, `with_company`) over generic key-value setters.

## Determinism And Flakiness
- Do not hide random UI path selection in default scenarios.
- If a feature supports random and explicit variants (e.g. random pickup point vs selected by id), create separate case IDs and keep both intentional.
- Avoid time-based or environment-dependent branching inside generator functions.

## Reuse And Backward Compatibility
- Prefer shared generator APIs from this package in tests instead of ad-hoc inline case objects.
- When renaming public generator functions, keep a short-term compatibility alias to avoid breaking existing tests.
- Export public generator helpers in package `__init__.py` modules.

## Security And Environment Data
- Treat `prod_*` test users as environment-specific compatibility helpers.
- Do not add new hardcoded production-like credentials unless explicitly requested.

## Quality Gate For Changes In This Layer
- After edits, run at minimum:
  - `python -m compileall qa/e2e/netcorner/nuxt/pl/lib/test_data qa/e2e/netcorner/nuxt/pl/tests`
