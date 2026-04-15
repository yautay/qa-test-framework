# Selector And Assertion Rules (E2E)

## Selector priority

1. `data-name`, `data-role`, stable `data-*`
2. semantic attributes (`href`, `title`, `id`) when stable
3. text only when no stable `data-*` is available
4. CSS classes only as a last resort

## Selector rules

- Keep selectors in components (not in tests).
- Prefer short, resilient selectors.
- Avoid layout-dependent selectors (for example `nth-child`) unless required.

## Action rules

- Execute UI actions via `BaseComponent`:
  - `safe_click`
  - `safe_type`
  - `safe_fill`
- Ensure elements are visible/ready before action.

## Steps API

- Decorate public PO methods that perform actions/assertions with `@step(...)`.
- Keep step descriptions at business-intent level (for example "Open login modal").

## Component class guidance

- For **Component class construction only**, align with recommendations from `qa-test-tools/lokomokopom`.
- Apply that guidance only to component-layer structure and API design.
- Do not transfer plugin-specific rules to pages, sections, wrappers, or test-layer conventions unless explicitly needed.

## Assertion rules

- Keep business assertions in tests.
- Keep helper UI assertions in components (`expect_*`, `should_*`) when useful.
- Use `expect(...)` and explicit timeouts where needed.
- Keep assert messages short and diagnostic.

## Wait strategy

- Prefer state-based waits (`to_be_visible`, `to_have_url`, `wait_for_load_state`).
- Do not add blind `wait_for_timeout` unless technically necessary.

## Good vs bad

Good:

```python
home = HomePage(page, runtime_env.base_url).open().wait_loaded()
home.header.actions.open_login()
```

Bad:

```python
page.goto(runtime_env.base_url)
page.locator('[data-name="loginDialogTrigger"]').click()
```
