# E2E POM Contract

This contract is mandatory for AI agents creating E2E tests.

## Mandatory access chain

- `page.section.component.method`

Example:

```python
home = HomePage(page, runtime_env.base_url).open().wait_loaded()
home.header.actions.open_login()
home.overlays.login.log_client(user.email, user.password)
```

## Layer responsibilities

- `Page`
  - represents a screen/URL and composes sections (`header`, `content`, `navigation`, `footer`).
  - `wait_loaded()` verifies section visibility.
- `Section`
  - container for domain components (for example `content.register_form`, `header.actions`).
- `Component`
  - contains selectors and action/assertion methods.
  - uses `BaseComponent` (`safe_click`, `safe_type`, `expect`).
- `Method`
  - a single business/UI intention (click, fill, verify).

## Minimalism rule (hard)

- Add only POM objects used by the new test.
- Do not create unused:
  - `Page` classes,
  - `Section` classes,
  - `Component` classes,
  - component methods.

## Component implementation rules

- Keep selectors in `__init__` as private fields (`self.__...`).
- Component public API should be business methods (`open_*`, `fill_*`, `expect_*`, `should_*`).
- Public methods must be decorated with `@step(...)` from `qa.e2e.netcorner.nuxt.pl.lib.allure_decorators.step`.
- Return `self` when method chaining is meaningful.
- For **Component classes only**, apply recommendations from `qa-test-tools/lokomokopom` where applicable.

## Steps API (hard)

- In PO classes (`pages/sections/components/overlays`), use Steps API exactly like current code.
- Import:

```python
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
```

- Every public method performing UI actions/assertions should have `@step("...")`.
- Private methods (`__...`) may remain undecorated, but should be wrapped by a public `@step(...)` method.
- Do not move step logic into tests when a component is the natural place.

Example:

```python
class HeaderActionsComponent(BaseComponent):
    @step("Open login modal")
    def open_login(self) -> None:
        self.safe_click(self.__login)
```

## What NOT to do

- Do not use `page.locator(...)` directly in tests.
- Do not duplicate existing component logic in a new component.
- Do not create "mega methods" that mix multiple independent responsibilities.
- Do not add new framework helpers when existing `BasePage`/`BaseComponent` is enough.

## When to create a new class

- New `Page`: only when the test covers a new screen and no equivalent exists.
- New `Section`: only when the screen has a new logical container that is actually used.
- New `Component`: only when actions/assertions do not fit existing components.

## Naming conventions

- Pages: `SomethingPage` in `page_objects/pages/`.
- Sections: `SomethingSection` in `page_objects/sections/`.
- Components: `SomethingComponent` in `page_objects/components/`.
- Tests: `test_<area>.py`, function names `test_<scenario>()`.
