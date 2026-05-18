# Visual Regression Tests Guide

This guide defines one clear approach for authoring visual scenarios in `qa/visual/**`, especially when deciding between JSON `steps` and POM-driven setup from Python tests.

## Goal
- Keep each scenario deterministic.
- Avoid accidental navigation resets before screenshot.
- Make ownership explicit: either JSON prepares state, or test/POM prepares state.

## Scenario Preparation Modes

Use `navigation_mode` in scenario JSON:

- `"navigation_mode": "auto"` (default)
  - Runner navigates to `target_url` before executing `steps`.
  - Best for self-contained visual scenarios.

- `"navigation_mode": "prepared"`
  - Runner does **not** navigate to `target_url`.
  - Use when state is prepared in test code (usually with POM).
  - Runner only executes scenario `steps` (if any) and captures screenshot.

## When To Use JSON Steps

Prefer `steps` when:
- Setup is simple and local to one screen.
- Actions are stable and do not require complex business flow.
- You want fully declarative, self-contained visual scenarios.

Recommended step style:
- Wait first, then act (`wait_for_selector` before `click`/`fill`).
- Use visible locators for interactive elements (`:visible` where needed).
- Keep selectors narrow and semantic (`data-*` attributes preferred).
- Use explicit `timeout_ms` for flaky/async UI.

## When To Use POM

Prefer POM preparation when:
- Entering target state requires reusable business flow.
- Flow spans overlays/pages and is already covered by E2E page objects.
- You need consistency with existing E2E abstractions.

Rules for POM-driven visual tests:
- Prepare screen in Python test before `execute_visual_scenario(...)`.
- Scenario JSON must use `"navigation_mode": "prepared"` to avoid post-POM `goto(...)`.
- Pass fixture `base_url` into page objects (not raw `runtime_env.base_url`), to stay aligned with target resolution.

## Decision Matrix

- `steps + auto`:
  - Scenario is independent and reproducible from `target_url`.
- `POM + prepared`:
  - Scenario depends on higher-level flow prepared in test code.
- `POM + steps + prepared`:
  - Valid when POM gets you close, and JSON `steps` finalize micro-state.

## Example Patterns

### A) Pure JSON scenario

```json
{
  "id": "vrt-example-login-layer",
  "target_url": "/",
  "navigation_mode": "auto",
  "steps": [
    { "action": "wait_for_selector", "selector": "[data-name='loginDialogTrigger']:visible", "timeout_ms": 10000 },
    { "action": "click", "selector": "[data-name='loginDialogTrigger']:visible", "timeout_ms": 10000 },
    { "action": "wait_for_selector", "selector": "[data-name='loginForm']:visible", "timeout_ms": 10000 }
  ]
}
```

### B) POM-driven scenario

```json
{
  "id": "vrt-example-register-layer",
  "target_url": "/register",
  "navigation_mode": "prepared",
  "steps": []
}
```

```python
if scenario.scenario_id == "vrt-example-register-layer":
    HomePage(page, base_url).open().wait_loaded().open_register_page()

execute_visual_scenario(...)
```

## Anti-Patterns (Do Not Do)
- POM preparation with `navigation_mode: "auto"` when runner should stay on prepared state.
- Relying on hidden or overly generic selectors for clicks.
- Mixing unrelated multi-page business flow into JSON `steps`.
- Adding fallback chains in POM locators that hide UI regressions.

## Validation Checklist
- Scenario has explicit `navigation_mode` when using POM.
- Visual screen before capture is exactly the intended final state.
- Locators are stable and visible-state aware.
- Focused run passes for the changed suite, e.g.:
  - `pytest -q qa/visual/netcorner/nuxt/pl/layers/test_layers_visual.py -vv`
