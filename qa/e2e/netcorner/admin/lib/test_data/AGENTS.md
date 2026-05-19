## Scope
- This file applies to `qa/e2e/netcorner/admin/lib/test_data/` and all nested folders.
- Keep this layer focused on typed test contracts and reusable scenario inputs.

## Structure And Ownership
- `*_models.py` or equivalent: data contracts only (`dataclass`, `Enum`, typed aliases).
- Keep mutable test setup outside models.
- Keep tests free from large inline ad-hoc data blocks when reusable models exist.

## Data Contract Rules
- Keep model fields explicit, typed, and deterministic.
- Prefer semantic field names aligned with admin domain language.
- Do not encode UI traversal logic inside data objects.

## Parametrization Guidance
- Prefer stable case objects with explicit identifiers when adding variants.
- Keep case IDs deterministic and descriptive.
- Avoid environment-dependent branching in case generation.

## Determinism And Flakiness
- Do not hide randomness in defaults that changes scenario behavior.
- Use randomness only where uniqueness is required and bounded.
- Keep values predictable for assertion readability.

## Reuse And Compatibility
- Prefer shared helper/model APIs from this package over one-off inline structures.
- When renaming public data helpers, keep compatibility aliases when practical.

## Verification
- Minimum after changes:
  - `python -m compileall qa/e2e/netcorner/admin/lib/test_data`
