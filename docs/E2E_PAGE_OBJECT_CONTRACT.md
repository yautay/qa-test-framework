# E2E Page Object Contract

This document is the normative contract for contributors and agents working in `qa/e2e/**`.

`docs/PAGE_OBJECTS_PL.md` and `docs/PAGE_OBJECTS_EN.md` stay as broader learning guides. When there is any conflict, this contract wins.

## Scope

This contract applies to:

- page objects in `qa/e2e/**/page_objects/`
- overlays, sections, and components
- wrappers and flows when they interact with page objects
- code written by humans and by coding agents

## Root Contract

Every page object owns a root boundary.

- A component interacts only inside `self.root`.
- A section exposes child components from its own root.
- A page may create sections or overlays, but a component should not escape to `page` just to find its own elements.
- If a component needs a root selector, resolve it explicitly from the provided scope.
- If a constructor receives the exact root locator, that locator may be reused directly.
- Do not silently fall back from a missing child root to an unrelated parent scope.

## Locator Contract

Use the simplest stable locator that matches the UI contract.

Preferred order:

1. Stable domain attributes such as `data-name`, `data-role`, `data-picker`
2. Semantic Playwright locators such as `get_by_role(...)`, `get_by_label(...)`, `get_by_text(...)`
3. Stable business text when it is the real UI contract
4. CSS or XPath only when there is no better option

Inside a component constructor:

- Use `self.find(...)` for first-level descendants of `self.root`
- Use `self.root.get_by_*` for semantic locators scoped to the root
- Cache a meaningful parent locator and use `parent.locator(...)` or `parent.get_by_*` for nested structures
- Do not start from `self.root.page` or `page` unless the code is intentionally leaving the component boundary

## Composition Pattern

Use these patterns consistently:

```python
class ExampleComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='example']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Example Component")

        self.__save_button = self.root.get_by_role("button", name="Save")
        self.__details_panel = self.find("[data-name='details']")
        self.__name_input = self.__details_panel.get_by_label("Name")
```

This is preferred over flattening everything into one long selector or bouncing between unrelated scopes.

## No-Fallback Policy

Do not add new silent fallback chains.

Avoid patterns like:

- `if locator.count() == 0: use_other_locator`
- `try primary selector except Exception: use_backup_selector`
- `trial=True` before the real click when the same helper already validates visibility and enabled state
- `if child root missing: return parent scope`
- parsing a large text blob because the intended field locator was not defined clearly

These patterns hide selector drift, make failures ambiguous, and slow down maintenance.

## Allowed Resilience

Resilience is allowed only when it models a real UI contract.

Allowed examples:

- optional UI that may or may not appear, such as a login modal
- bounded waiting for async state changes
- explicitly supported layout variants, such as a documented list layout and matrix layout

Even then:

- keep the logic explicit
- keep retries bounded
- fail with a clear error when the contract is not met

## Click And Input Rules

- Prefer shared helpers such as `pointer_click(...)`, `safe_fill(...)`, and `safe_type(...)`
- Do not stack redundant pre-checks around those helpers unless the code needs a clearer domain-specific error
- Do not create alternate click paths for the same element without evidence that the UI contract requires it

## DOM Capture Contract

When pytest runs with `--collect_dom` (or `--collect-dom`), page object code must support consistent DOM snapshots for AI analysis.

- Primary capture trigger is page-level `wait_loaded(...)`.
- The canonical page identifier is class constant `PAGE_ID`.
- `PAGE_ID` format is `netcorner.pl.<area>.<view>` and should be stable across refactors.
- If a UI transition does not go through a page object `wait_loaded(...)` but is important for analysis, capture may be triggered explicitly with a bounded event name.
- Avoid noisy over-capture; prefer meaningful lifecycle points.

Expected artifact structure:

- `artifacts/<run_id>/dom/<nodeid_safe>/`
- snapshot files: `<seq>__<event>__<page_id>__<url_token>__<viewport>.html.gz`
- metadata index: `index.jsonl`

## Error Handling

- Prefer fail-fast behavior over silent fallback
- Catch only expected exception types
- Do not use broad `except Exception` to hide locator or DOM contract problems
- Error messages should explain which contract failed, not just that something "did not work"

## Review Checklist

Before merging a page object change, verify:

- the root boundary is clear
- locators are scoped to the right root
- new code does not add silent fallback chains
- semantic Playwright locators are used when they are the clearest option
- nested locators are expressed through cached parent locators
- the test API exposes intent, not raw locators

## Agent Instructions

Agents changing `qa/e2e/**` must follow these rules:

- read this document before refactoring page objects
- do not introduce new fallback chains to "make tests pass"
- when touching legacy code, migrate the touched area toward this contract
- update `docs/PAGE_OBJECTS_PL.md` and `docs/PAGE_OBJECTS_EN.md` when the teaching examples drift from the real contract
- prefer small, local refactors that tighten scope and remove ambiguity

## Polling And Backend Waits

Backend polling (waiting for a mail to arrive, a counter to update, an admin state to change) has a dedicated contract separate from Playwright UI waits.

### Primitives

- `framework.polling.poll_until(fn, *, condition, timeout_s, poll_s, default)` — generic backend poller. Calls `fn()` repeatedly until `condition(result)` is truthy or `timeout_s` elapses. Returns the last value; the caller owns the assertion.
- `framework.polling.HttpPoller` — thin wrapper around `poll_until` for HTTP JSON endpoints. Uses `urllib.request` with unverified SSL (standard for internal test environments). Use `HttpPoller.poll(url, condition=...)` for endpoint polling.

### Decision Table

| Situation | Correct tool |
|---|---|
| Waiting for a DOM element to appear or become visible | `expect(locator).to_be_visible(...)` |
| Waiting for a page to finish loading | `wait_loaded()` / `wait_for_load_state(...)` |
| Waiting for a Mailhog mail to arrive (count check) | `MailhogApiClient.wait_for_mails_containing_text(...)` via `HttpPoller` |
| Waiting for an OZO counter or admin state to change | `poll_until(fn, condition=..., ...)` |
| Waiting for a mail link to be readable (content) | `MailInboxService.get_*_link(...)` — polling is inside the flow via `__open_message` |

### Rules

- Do **not** write `while + time.sleep` or `for _ in range(n): ... sleep(...)` loops in tests or flows. Use `poll_until` instead.
- Do **not** call `urllib.request.urlopen` directly in test or flow code. Use `HttpPoller`.
- `poll_until` / `HttpPoller` are for **backend resources only**. For Playwright UI readiness always use `expect(...)`, `wait_loaded()`, or `wait_visible()`.
- Keep `timeout_s` and `poll_s` explicit at the call site or named constants — never hardcode magic numbers inline.

