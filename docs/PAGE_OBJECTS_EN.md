# Page Objects Guide

This document is for people who know manual testing well but are just starting with automation. If you can already write a test scenario step by step, you already have the right foundation. A page object is simply a way to express that scenario in code so the test stays readable, stable, and easy to maintain.

In this repository, page objects are used heavily in `qa/e2e/netcorner/nuxt/pl/lib/page_objects/`.

The normative contributor and agent contract lives in `docs/E2E_PAGE_OBJECT_CONTRACT.md`.
This document remains a teaching guide. If an example ever drifts from the contract, the contract wins.

## Why we use page objects

Without page objects, a test quickly turns into a list of selectors and clicks:

```python
page.locator("#login").fill("user@example.com")
page.locator("#password").fill("secret")
page.get_by_role("button", name="Log in").click()
```

This works, but it has a few problems:

- the test knows too much about HTML,
- selectors are scattered across many files,
- when the UI changes, many tests need to be updated,
- it becomes hard to separate business logic from browser mechanics.

With a page object, the same intent looks like this:

```python
home.open_login_overlay().log_client(user.email, user.password)
```

Now the test says what we do from a business point of view, not how the DOM is built.

## How to think about the architecture in this repo

The simplest mental model is:

`Page -> Section -> Component -> Overlay -> Flow/Wrapper`

Each layer has a different responsibility.

## 1. Page

`Page` represents a full screen or application view.

Examples:

- `HomePage`
- `ListingPage`
- `ProductPage`
- `CartPage`
- `CheckoutPage`

A page usually:

- knows its `PATH`,
- can open itself and wait until the screen is ready,
- exposes sections like `header`, `content`, `footer`,
- provides navigation methods that return another page object or an overlay.

Example from this repo:

```python
class HomePage(BasePage):
    PATH = "/"

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> HomePage:
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
        self.navigation.wait_visible()
        self.content.wait_visible()
        self.footer.wait_visible()
        return self

    def open_register_page(self) -> RegisterPage:
        self.open_login_overlay().enter_register_form()
        return RegisterPage(self.page, self.base_url).wait_loaded()
```

This is a very good pattern:

- `wait_loaded()` verifies that the screen is really ready,
- `open_register_page()` returns a new page object because the screen context changes.

## 2. Section

`Section` groups a larger part of the page.

Typical examples:

- `HeaderSection`
- `NavigationSection`
- `ContentSection`
- `FooterSection`

A section should not hold the whole business flow. Its job is to organize components inside one logical part of the screen.

Example:

```python
class HeaderSection(BaseComponent):
    def __init__(self, page: Page):
        self.__header_root = HeaderComponent(page)
        super().__init__(self.__header_root.root, name="Header Section")
        self.__search_bar: SearchBarComponent | None = None
        self.__actions: HeaderActionsComponent | None = None

    @property
    def actions(self) -> HeaderActionsComponent:
        if self.__actions is None:
            self.__actions = HeaderActionsComponent(self.root)
        return self.__actions
```

So:

- the section has its own root,
- inside it exposes smaller components,
- the test or page object does not need to know DOM details.

## 3. Component

`Component` is the most important building block. It represents a specific UI element: a form, table, product tile, price block, filters, payment panel.

A good component:

- has one clear responsibility,
- works only inside its own root,
- hides selectors,
- exposes simple methods like `fill_...`, `click_...`, `get_...`, `set_...`.

Example:

```python
class RegisterClientComponent(BaseComponent):
    ROOT_SELECTOR = "form"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Register Client Component")
        self.__input_login = self.find("#login")
        self.__input_password = self.find("#password")
        self.__button_register = self.find('button:has-text("Create account")')

    @step("I enter customer login: {email}")
    def fill_login(self, email: str) -> Self:
        self.safe_type(self.__input_login, email)
        return self

    @step("I click the 'Create account' button")
    def submit_registration(self) -> None:
        self.pointer_click(self.__button_register)
```

This is the style we want:

- selectors are private,
- method names describe intent,
- the `@step(...)` decorator creates readable reporting,
- mutating methods on the same component can return `Self`.

## 4. Overlay

`Overlay` is a modal, popup, toast, or any layer displayed above the page.

Examples:

- `LoginOverlay`
- `PasswordRecoveryOverlay`
- `ToastOverlay`
- checkout overlays

An overlay should have its own object because:

- it has a different root than the page,
- it appears conditionally,
- it often has its own open/close logic.

Example:

```python
class LoginOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="loginForm"]:visible').first, name="Login Overlay")
        self.__input_login = self.find("#loginEmail")
        self.__button_login = self.root.get_by_role(role="button", name="Log in")

    @step("I log in with login: {client_login} and password: {client_pwd}")
    def log_client(self, client_login: str, client_pwd: str) -> None:
        self.safe_type(self.__input_login, client_login)
        self.safe_type(self.__input_password, client_pwd)
        self.pointer_click(self.__button_login)
```

## 5. Flow / Wrapper

`Flow` or `Wrapper` is a higher level than a page object. We use it when the scenario goes through multiple screens and we want a business-level description of the whole process.

Examples from this repo:

- `ClientWrappers`
- `SelectProductWrappers`
- `CartAndCheckoutWrappers`

A wrapper is a good fit when:

- the scenario is long,
- it repeats in many tests,
- it spans multiple page objects,
- you want the test to stay short and readable.

Example:

```python
with step_context("I open the home page"):
    home = HomePage(self.__page, self.__runtime_env.base_url)
    home.open().wait_loaded()

with step_context("I open the login panel and choose the registration form"):
    register_page = home.open_register_page()
```

So:

- the page object is responsible for the screen,
- the wrapper is responsible for the whole business flow.

## When to create a Page and when only a Component

Ask one simple question: does the user land on a separate screen, or are they only interacting with part of an existing screen?

Create a `Page` when:

- there is a separate URL,
- the full screen context changes,
- the screen needs its own `wait_loaded()`.

Create a `Component` when:

- it is a fragment of a page,
- it works inside an existing screen,
- it has its own actions and data reads, but it is not a separate view.

Create an `Overlay` when:

- something appears above the page,
- it does not belong logically to the main page layout,
- closing it returns you to the same page.

## Where to place classes in directories

In practice, we use this split:

- `page_objects/pages/` - full screens
- `page_objects/sections/` - larger areas of a screen
- `page_objects/components/` - smaller, specific UI elements
- `page_objects/overlays/` - modals, popups, toasts
- `lib/flows/` - larger business processes built on top of page objects

If you are unsure where a new class belongs, first answer: is it a screen, an area, a widget, or a popup?

## Base classes used in this repo

### `BasePage`

The local `BasePage` extends the framework base class and adds access to `overlays`.

```python
class BasePage(FrameworkBasePage):
    @property
    def overlays(self):
        if self._overlays is None:
            self._overlays = Overlays(self.page)
        return self._overlays
```

This means that from any page object you can do:

```python
home.overlays.login.wait_visible()
```

### `BaseComponent`

The local `BaseComponent` adds the helper `resolve_root(...)`.

```python
class BaseComponent(FrameworkBaseComponent):
    @staticmethod
    def resolve_root(scope: Page | Locator, root_selector: str) -> Locator:
        if isinstance(scope, Page):
            return scope.locator(root_selector)
        if scope.evaluate("(node, selector) => node instanceof Element && node.matches(selector)", root_selector):
            return scope
        return scope.locator(root_selector)
```

In practice, this gives us a very convenient constructor pattern:

```python
class SomeComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='someComponent']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Some Component")
```

Because of this, the component works both when it receives `Page` and when it receives the root of a section or another component.

New constructor locator rule:

- `self.find(...)` for first-level descendants of `self.root`
- `self.root.get_by_*` for semantic Playwright locators
- `parent.locator(...)` or `parent.get_by_*` only for intentional nested structures
- no silent `A -> B -> C` fallback chains unless the UI exposes an explicit supported variant

## The most important rules for method design

### 1. Method names should describe business intent

Good names:

- `open_login_overlay()`
- `open_register_page()`
- `fill_password()`
- `choose_payment_method()`
- `get_available_payment_methods()`
- `set_electronic_invoice(True)`

Weak names:

- `click_button1()`
- `do_action()`
- `handle_form()`
- `process()`

It should be clear from the method name what the user is doing.

### 2. A method should do one thing

Do not mix these in one method:

- entering data,
- clicking submit,
- verifying the full business outcome.

This split is better:

```python
form.fill_login(user.email)
form.fill_password(user.password)
form.submit_registration()
```

than this:

```python
form.register_user(user)
```

Exception: if the higher-level action truly represents a business flow, move it into a wrapper, not into a low-level component.

### 3. In-place actions return `Self`

If the method keeps you on the same component, return `Self`.

Example:

```python
@step("I accept required terms")
def accept_required_terms(self) -> Self:
    self.pointer_click(self.__checkbox_terms)
    return self
```

This allows readable chaining:

```python
register_page.content.register_form.fill_login(email).fill_password(password).accept_required_terms()
```

### 4. Context changes return a new object

If an action moves you to another screen, return a new `Page` or `Overlay`.

Example:

```python
def open_register_page(self) -> RegisterPage:
    self.open_login_overlay().enter_register_form()
    return RegisterPage(self.page, self.base_url).wait_loaded()
```

### 5. Data reads return data, not locators

The test should not know locators. The test should receive information.

Good return values:

- `bool`
- `str`
- `Decimal`
- `dataclass`
- `tuple[...]`, when it really makes sense

In this repo, we often use `dataclass` for things like product data or payment methods.

## When to use `dataclass`

If a screen returns a set of values, `dataclass` is usually a very good choice.

Example:

```python
@dataclass(frozen=True, slots=True)
class PaymentMethodData:
    name: str
    surcharge: Decimal
```

Benefits:

- the test receives a clear object,
- fields are named,
- expectations are easier to compare against UI data,
- the code is more self-descriptive than a plain list or untyped dict.

## How to write selectors

This is one of the most important parts for test stability.

Preferred order:

- stable attributes like `data-name`, `data-role`, `data-picker`,
- semantic Playwright selectors like `get_by_role(...)`,
- readable text, if it is stable from a business perspective,
- CSS/XPath only when there is no better option.

Good examples from this repo:

- `[data-name="orderPickerTile"]`
- `[data-picker="paymentMethod"]`
- `get_by_role("button", name="Log in")`

Try to:

- always search inside the component root,
- avoid very long selectors that describe half the page,
- avoid selectors based on random CSS classes when domain-specific attributes exist.

## `step` and `step_context` - very important rule

In this repo, `step` must always be imported from:

```python
from qa.e2e.netcorner.lib.step_api import step, step_context
```

Do not import `allure.step` directly.

The reason is simple:

- the repo has its own wrapper,
- the wrapper records steps not only to Allure but also to the internal test trace,
- that keeps reporting consistent.

Use:

- `@step(...)` for methods,
- `with step_context(...)` for larger blocks inside wrappers and flows.

Component example:

```python
@step("I choose payment method: {payment_method}")
def choose_payment_method(self, payment_method: PaymentMethods) -> Decimal:
    ...
```

Wrapper example:

```python
with step_context("I open the home page"):
    home = HomePage(self.__page, self.__runtime_env.base_url)
    home.open().wait_loaded()
```

## `wait_loaded()` and `wait_visible()`

People who are new to automation often try to fight instability using `sleep(...)`. In this repo, we do not want that.

Instead:

- a page should have its own `wait_loaded()`,
- a component or section should have a meaningful `wait_visible()`,
- after a transition to a new screen, return the object after `wait_loaded()` whenever possible.

This way the test does not guess when the UI is ready.

## Page-level API - the preferred style

If a scenario is naturally understood as a transition between screens, keep that transition logic on the page level, not in the test.

Better style:

```python
register_page = home.open_register_page()
account_page = home.open_account_page()
configurator_page = home.open_configurator_from_banner()
```

Weaker style:

```python
home.header.actions.open_login()
home.overlays.login.enter_register_form()
register_page = RegisterPage(page, base_url).wait_loaded()
```

The second version works, but the test knows too many implementation details. If the registration entry flow changes, you want to update one page object, not many tests.

## Step by step: how to add a new page object

### Step 1. Write the scenario as if it were a manual test

Example way of thinking:

1. The user opens the product page.
2. They see the price block.
3. They click "Add to cart".
4. The system shows a popup or changes the page state.

This already suggests the structure:

- `ProductPage`
- `ProductPriceComponent`
- maybe an overlay after adding to cart

### Step 2. Find the component root

Do not start from one single input. First find the logical container, for example:

- a form,
- a price block,
- a table,
- a payment section.

Then define `ROOT_SELECTOR` in the component.

### Step 3. Build the component

Minimal template:

```python
from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class ExampleComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='example']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Example Component")
        self.__input_name = self.find("#name")
        self.__button_save = self.find("button:has-text('Save')")

    @step("I enter name: {name}")
    def fill_name(self, name: str) -> Self:
        self.safe_type(self.__input_name, name)
        return self

    @step("I save the form")
    def save(self) -> None:
        self.pointer_click(self.__button_save)
```

### Step 4. Connect the component to a section

```python
class ExampleContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__example: ExampleComponent | None = None

    @property
    def example(self) -> ExampleComponent:
        if self.__example is None:
            self.__example = ExampleComponent(self.root)
        return self.__example
```

### Step 5. Connect the section to a page

```python
class ExamplePage(BasePage):
    PATH = "/example"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: ExampleContentSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> ExamplePage:
        super().wait_loaded(state=state, timeout=timeout)
        self.content.wait_visible()
        return self

    @property
    def content(self) -> ExampleContentSection:
        if self.__content is None:
            self.__content = ExampleContentSection(self.page)
        return self.__content
```

### Step 6. Add a page-level method if the transition makes business sense

If a page can naturally open another screen, hide that logic in the page object.

```python
def open_summary_page(self) -> SummaryPage:
    self.content.example.save()
    return SummaryPage(self.page, self.base_url).wait_loaded()
```

### Step 7. Only then use it in the test or wrapper

```python
example_page = ExamplePage(page, runtime_env.base_url).open().wait_loaded()
example_page.content.example.fill_name("Alice")
summary_page = example_page.open_summary_page()
```

## What a good test looks like with page objects

A test should describe the scenario, not HTML.

Good direction:

```python
def test_basic_orders(page, context, runtime_env, auth_case, delivery_case):
    _prepare_client_session(page, context, runtime_env, auth_case)
    selected_product = SelectProductWrappers(page, context, runtime_env).select_test_product(
        first_aviable_laptop_case()
    )
    assert selected_product is not None
    assert selected_product.product_page_data is not None

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_wrappers.process_checkout(
        delivery_case.delivery_type,
        delivery_case.delivery_objects,
        delivery_case.purchaser_objects,
        delivery_case.payment_objects,
    )
```

Here the test shows the ordering process, not the DOM structure. That is exactly the goal of page objects and wrappers.

## What not to do

### Do not expose locators to tests

This is a bad direction:

```python
test_page.content.form.submit_button.click()
```

The test should not know that `submit_button` exists. The test should call a method like `submit_registration()`.

### Do not duplicate the same helpers across many classes

If several components need the same logic, move it to a shared helper. In this repo, for example, we have `page_objects/utils.py`.

### Do not create two different APIs for the same action

If the action "go forward in the cart" is already available through the footer, do not build another separate object that does exactly the same thing through a different route. One responsibility, one obvious API.

### Do not import `step` directly from Allure

Use only the wrapper from `qa.e2e.netcorner.lib.step_api`.

### Do not put the whole business flow into a component

A component should manage a UI fragment. If the scenario spans multiple screens, use a wrapper.

### Do not use `sleep(...)` when you can wait for UI state

Try these first:

- `wait_loaded()`
- `wait_visible()`
- `expect(...)`
- helpers like `pointer_click`, `safe_fill`, and `safe_type`

## When to add assertions inside a page object

This is a common question.

A good rule is:

- a page object may perform small technical checks needed for stability,
- the main business assertions should stay in the test.

Technical checks are fine, for example:

- after clicking a checkbox, verify that a field becomes visible,
- verify that a component exists before interacting with it,
- validate that a delivery layout can be recognized.

But comparing an expected price with the displayed price usually belongs in the test or wrapper, not inside a low-level component.

## How to write readable report steps

Write step titles in the language of the user action, not the language of implementation.

Good examples:

- `I enter customer login: {email}`
- `I click the delivery tile: Courier delivery`
- `I accept required terms`

Weak examples:

- `Set login input`
- `Click submit btn`
- `Handle delivery`

Someone reading the report should understand what happened in the application.

## Typing and return style

In this repo, it is worth following these rules:

- add types to arguments and return values,
- if a method may return no result, mark it with `| None`,
- use `Self` for in-place methods,
- use `dataclass(frozen=True, slots=True)` for simple UI data objects,
- avoid `Any` when a concrete type is easy to define.

## Checklist before you finish a new page object

Before you consider the work done, check:

- is the class in the right directory,
- does it have a good root,
- are the selectors stable,
- do the methods have meaningful names,
- do in-place actions return `Self`,
- do transitions between screens return a new page object,
- do data reads return types or dataclasses instead of locators,
- are you using `step` and `step_context` from our wrapper,
- does the test use the page object instead of raw selectors,
- could the API be simpler on the page level,
- did you avoid duplicating an existing responsibility,
- does the code pass at least minimal validation.

## How to verify changes

After changing page objects, the minimum is:

```bash
python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests
```

If the change affects a real scenario, also run a matching test or suite, for example:

```bash
python -m pytest qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py -q
```

Broader framework-level validation:

```bash
make test-aso
```

## Short cheat sheet

If you remember only a few things, remember these:

- the test should talk about the scenario, not selectors,
- the page object should hide technical UI details,
- a component should have one responsibility,
- a page should expose natural transitions between screens,
- a wrapper should handle longer business flows,
- `step` comes from `qa.e2e.netcorner.lib.step_api`, not directly from Allure,
- UI data should be returned as typed values or `dataclass`, not as locators,
- a stable root and good selectors matter more than clever code.

If you are creating a new page object and do not know where to start, start like a manual tester: describe the screen, describe the user actions, name the intent, and only then turn that into classes and methods.
