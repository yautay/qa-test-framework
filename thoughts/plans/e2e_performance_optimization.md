# E2E Performance Optimization - Implementation Plan

## Overview

Optimize E2E test execution from 60-360s/test to 60-90s/test by eliminating the `first_visible()` protocol call explosion in `BaseComponent`, replacing manual polling with Playwright auto-waiting, adding configurable tracing, and reducing hard sleeps in flow code. All changes are big-bang in-place modifications to existing classes.

## Current State Analysis

### Root Cause Chain
Every component creation triggers `resolve_root` → `first_visible()` which iterates DOM elements calling `is_visible()` individually via Playwright protocol. With 35-80 components per test, `find()` re-running `first_visible()` on every call (e.g. `CartProductComponent` has 10 `find()` calls), and `_resolve_visible_root` polling every 100ms, this produces 500-2000+ protocol round-trips per test.

### Key Discoveries
- `find()` re-resolves root on every call via `first_visible()` (`framework/base/page_objects/base_component.py:91-93`) - **biggest amplifier**
- `first_visible()` does `count()` + N×`is_visible()` protocol calls (`framework/base/page_objects/base_component.py:18-32`)
- `_scope_matches_root()` adds JS `evaluate()` round-trip per Locator-scoped component (`qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py:10-11`)
- `_resolve_visible_root()` polls every 100ms with full `first_visible()` re-scan (`framework/base/page_objects/base_component.py:95-113`)
- Action methods (`pointer_click`, `safe_fill`, `safe_type`, `non_pointer_click`) each call `first_visible()` again (`framework/base/page_objects/base_component.py:53-85`)
- 30 of 33 component classes use `resolve_root` in constructors
- Only 2 ROOT_SELECTORs use comma-separated selectors; the mobile/desktop duplication is in the **DOM** (Nuxt renders hidden mobile variants of same `data-name` elements), not in selector design
- Tracing is always-on with `screenshots=True, snapshots=True, sources=True` (`qa/e2e/conftest.py:189`)
- Hard sleeps: `sleep(3500)` checkout (`cart_and_checkout_wrappers.py:145`), `sleep(2000)` sorting (`listing_components.py:118`)

### Architecture (scope chain)
```
Page (lazy sections via @property)
  → Section (eager root component, lazy child components)
    → Component (resolve_root in __init__, find() for sub-locators)
```
- Pages pass `self.page` to sections
- Sections pass `self.root` (Locator) to components
- Components use `resolve_root(scope, ROOT_SELECTOR)` to build their root locator

## Desired End State

- `BaseComponent.find()` creates locators without re-resolving root (no `first_visible()` call)
- `first_visible()` replaced with `:visible` CSS pseudo-selector + `.first` (single locator, zero iteration)
- `_scope_matches_root()` JS eval eliminated
- `_resolve_visible_root()` polling replaced with Playwright `expect().to_be_visible()`
- Action methods use `expect()` auto-waiting instead of `first_visible()` loops
- Tracing configurable via `TRACE_ENABLED` env var (default: `True`)
- Hard sleeps in flows replaced with condition-based waits (overlay sleeps preserved)
- All existing E2E tests pass, ASO tests updated/added

### Verification
- `make test-aso` passes (unit tests for new BaseComponent behavior + tracing toggle)
- `make test-e2e` passes (regression)
- `make check` passes (lint, typecheck, format)
- `test_basic_orders` execution time consistently 60-90s/test in headless mode

## What We're NOT Doing

- Mobile viewport support in E2E (desktop-only, confirmed)
- Changing the Page → Section → Component architecture
- Modifying overlay sleep patterns (purchaser, courier, storehouse overlays keep their sleeps)
- xdist/grid optimization (separate effort, depends on SUT throughput)
- Test result caching
- CI integration for performance metrics (artifacts-only)
- Creating a new parallel component library (big-bang in-place instead)

## Implementation Approach

Big-bang modification of `BaseComponent` (both framework and E2E layers) and all dependent code. The key insight is replacing `first_visible()` iteration with Playwright's `:visible` CSS pseudo-selector, which filters visibility server-side in a single protocol call instead of N round-trips.

---

## Phase 1: Core BaseComponent Optimization

### Overview
Eliminate the `first_visible()` protocol call explosion by replacing it with `:visible` pseudo-selector filtering, removing `find()` re-resolution, and replacing polling with Playwright auto-waiting.

### Changes Required

#### 1. Framework BaseComponent
**File**: `framework/base/page_objects/base_component.py`
**Changes**: Complete rewrite of `first_visible`, `find`, `_resolve_visible_root`, and action methods.

**`__init__` - use `:visible` filtering instead of `first_visible()` iteration:**
```python
def __init__(self, root: Locator, name: str = "Component"):
    self._root_candidates = root
    self.root = self._pick_visible(root)
    self.name = name

@staticmethod
def _pick_visible(locator: Locator) -> Locator:
    """Return a single-element locator targeting the first visible match.

    Uses Playwright's built-in :visible pseudo-selector to filter
    server-side, avoiding O(N) is_visible() protocol round-trips.
    Falls back to .first if the :visible filter yields nothing
    (element not yet rendered).
    """
    visible = locator.locator(":visible").first
    return visible
```

**`find()` - stop re-resolving root:**
```python
def find(self, selector: str) -> Locator:
    return self.root.locator(selector)
```

Remove the `self.root = self.first_visible(self._root_candidates)` line entirely. `find()` becomes a simple locator chain with zero protocol calls.

**`_resolve_visible_root()` - replace polling with Playwright auto-wait:**
```python
def _resolve_visible_root(self, *, timeout: int) -> Locator:
    self.root = self._pick_visible(self._root_candidates)
    return self.root
```

The polling loop is removed entirely. `wait_visible()` and `assert_visible()` already call `expect(target).to_be_visible(timeout=t)` after `_resolve_visible_root`, which handles the waiting via Playwright's built-in retry mechanism.

**Action methods - use `expect()` auto-waiting instead of `first_visible()`:**
```python
def pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
    t = timeout or self.DEFAULT_TIMEOUT
    target = locator.locator(":visible").first
    expect(target).to_be_visible(timeout=t)
    expect(target).to_be_enabled(timeout=t)
    target.scroll_into_view_if_needed()
    target.click(timeout=t)
    return self

def non_pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
    t = timeout or self.DEFAULT_TIMEOUT
    target = locator.locator(":visible").first
    expect(target).to_be_visible(timeout=t)
    expect(target).to_be_enabled(timeout=t)
    target.scroll_into_view_if_needed()
    target.evaluate("node => node.click()")
    return self

def safe_fill(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
    t = timeout or self.DEFAULT_TIMEOUT
    target = locator.locator(":visible").first
    expect(target).to_be_visible(timeout=t)
    target.scroll_into_view_if_needed()
    target.fill(value, timeout=t)
    return self

def safe_type(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
    t = timeout or self.DEFAULT_TIMEOUT
    target = locator.locator(":visible").first
    expect(target).to_be_visible(timeout=t)
    target.scroll_into_view_if_needed()
    target.type(value, timeout=t)
    return self
```

**Remove `first_visible()` static method** - it is no longer called anywhere. Remove it or keep as deprecated with a `# DEPRECATED` comment for one release cycle if preferred.

**Full resulting file:**
```python
from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, expect


class BaseComponent:
    DEFAULT_TIMEOUT = 10_000

    def __init__(self, root: Locator, name: str = "Component"):
        self._root_candidates = root
        self.root = self._pick_visible(root)
        self.name = name

    @staticmethod
    def _pick_visible(locator: Locator) -> Locator:
        """First visible match via :visible pseudo-selector (single protocol op)."""
        return locator.locator(":visible").first

    def wait_visible(self, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self._resolve_visible_root(timeout=t)
        expect(target).to_be_visible(timeout=t)
        return self

    def wait_hidden(self, timeout: int | None = None) -> Self:
        expect(self.root).to_be_hidden(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def assert_visible(self) -> Self:
        target = self._resolve_visible_root(timeout=self.DEFAULT_TIMEOUT)
        expect(target).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        return self

    def assert_hidden(self) -> Self:
        expect(self.root).to_be_hidden(timeout=self.DEFAULT_TIMEOUT)
        return self

    def pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.locator(":visible").first
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.click(timeout=t)
        return self

    def non_pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.locator(":visible").first
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.evaluate("node => node.click()")
        return self

    def safe_fill(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.locator(":visible").first
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.fill(value, timeout=t)
        return self

    def safe_type(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.locator(":visible").first
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.type(value, timeout=t)
        return self

    def should_have_text(self, locator: Locator, text: str) -> Self:
        expect(locator).to_have_text(text, timeout=self.DEFAULT_TIMEOUT)
        return self

    def find(self, selector: str) -> Locator:
        return self.root.locator(selector)

    def _resolve_visible_root(self, *, timeout: int) -> Locator:
        self.root = self._pick_visible(self._root_candidates)
        return self.root

    def sleep(self, ms: int) -> Self:
        if ms < 0:
            raise ValueError("ms must be >= 0")
        self.root.page.wait_for_timeout(ms)
        return self
```

#### 2. E2E BaseComponent
**File**: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py`
**Changes**: Simplify `resolve_root` - remove `_scope_matches_root` JS eval entirely.

The `_scope_matches_root` check exists to avoid double-nesting locators when the scope already matches the root selector. With `:visible` filtering this optimization is less critical (the extra nesting adds no protocol calls since Playwright locators are lazy). However, it can still be useful to avoid confusing locator chains, so we keep a simplified version without JS eval:

```python
from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent as FrameworkBaseComponent


class BaseComponent(FrameworkBaseComponent):
    @staticmethod
    def resolve_root(scope: Page | Locator, root_selector: str) -> Locator:
        return scope.locator(root_selector)


__all__ = ["BaseComponent"]
```

The `_scope_matches_root` method and its JS `evaluate()` call are removed entirely. Even when scope is a Locator that already matches the root selector, the double-nesting is harmless because Playwright locators are lazy descriptors - `scope.locator(root_selector)` just builds a selector chain with zero protocol calls. The `:visible` filtering in `_pick_visible` will handle finding the correct element.

#### 3. Overlay common helper
**File**: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/overlays/checkout/common.py`
**Changes**: The `_is_visible` helper uses `locator.first` + `.count()` + `.is_visible()` pattern. This is used in purchaser overlay for conditional logic (not in hot loops), so it can stay as-is. No changes needed.

### Risk: `:visible` pseudo-selector behavior

The `:visible` pseudo-selector in Playwright filters based on CSS `visibility` and `display` properties, similar to `is_visible()` but evaluated server-side in a single call. Key considerations:

1. **Double `:visible` nesting**: When `_pick_visible` is called on a locator that was already built with `:visible` (e.g., overlay roots using `:visible` in their selector like `[data-name="OrderAddressDialog"]:visible`), nesting `locator(":visible").first` on top is harmless - Playwright combines the selectors.

2. **Empty match**: If no visible elements exist yet, `locator(":visible").first` returns a locator that points to nothing. Playwright's `expect().to_be_visible()` will auto-retry until the element appears or timeout. This is the desired behavior for `wait_visible()`.

3. **Stale visibility**: Since `_pick_visible` is called at component construction time, if the visible element changes after construction (e.g., tab switches), `find()` calls still use the original `self.root`. This matches the current behavior where `self.root` is also set once at construction.

### Success Criteria

#### Automated Verification
- [ ] `make test-aso` passes - existing `test_base_component_first_visible.py` tests updated
- [ ] `make check` passes (lint, typecheck, format)
- [ ] `make verify-discovery` passes (collection sanity)

#### Manual Verification
- [ ] `make test-e2e` full run completes without regressions
- [ ] `test_basic_orders` execution times measured and compared to baseline

---

## Phase 2: Configurable Tracing

### Overview
Add `TRACE_ENABLED` env var toggle (default: `True`) following the existing `RECORD_VIDEO` / `FAILED_DOM_ENABLED` pattern. Add ASO tests verifying the toggle works correctly and artifacts are produced when enabled.

### Changes Required

#### 1. Settings default
**File**: `settings.py`
**Changes**: Add `trace_enabled = True` in the Runtime section (after `failed_dom_enabled` at line 20).

```python
trace_enabled = True
```

#### 2. RuntimeEnv dataclass
**File**: `framework/env.py`
**Changes**: Add `trace_enabled: bool` field to `RuntimeEnv` dataclass (after `failed_dom_enabled` at line 104).

```python
trace_enabled: bool
```

#### 3. load_env() resolution
**File**: `framework/env.py`
**Changes**: Add env var resolution in the `RuntimeEnv(...)` constructor call (after `failed_dom_enabled` at line 320).

```python
trace_enabled=env_bool("TRACE_ENABLED", settings.trace_enabled),
```

#### 4. E2E context fixture
**File**: `qa/e2e/conftest.py`
**Changes**: Gate tracing start/stop on `runtime_env.trace_enabled` in the `context` fixture.

Current (line 189):
```python
context.tracing.start(screenshots=True, snapshots=True, sources=True)
```

New:
```python
trace_enabled = runtime_env.trace_enabled
if trace_enabled:
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
```

Current teardown (lines 204-216):
```python
if failed:
    trace_path = run_artifacts.traces / f"{nodeid_safe}.zip"
    context.tracing.stop(path=str(trace_path))
    artifacts_payload["trace"] = str(trace_path)
    ...
else:
    context.tracing.stop()
```

New:
```python
if trace_enabled:
    if failed:
        trace_path = run_artifacts.traces / f"{nodeid_safe}.zip"
        context.tracing.stop(path=str(trace_path))
        artifacts_payload["trace"] = str(trace_path)
        _allure_attach_file(
            pytestconfig,
            trace_path,
            name="trace",
            attachment_type="application/zip",
            extension="zip",
        )
    else:
        context.tracing.stop()
```

#### 5. ASO tests for tracing toggle
**File**: `qa/aso/framework/test_trace_toggle.py` (new file)
**Changes**: Unit tests verifying:
- `RuntimeEnv` resolves `trace_enabled` from `TRACE_ENABLED` env var
- Default is `True`
- `TRACE_ENABLED=0` sets it to `False`

```python
from __future__ import annotations

import pytest

from framework.env import load_env

pytestmark = [pytest.mark.aso]


def test_trace_enabled_defaults_to_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRACE_ENABLED", raising=False)
    env = load_env()
    assert env.trace_enabled is True


def test_trace_enabled_respects_env_var_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRACE_ENABLED", "0")
    env = load_env()
    assert env.trace_enabled is False


def test_trace_enabled_respects_env_var_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRACE_ENABLED", "1")
    env = load_env()
    assert env.trace_enabled is True
```

### Success Criteria

#### Automated Verification
- [ ] `make test-aso` passes with new `test_trace_toggle.py` tests
- [ ] `make check` passes

#### Manual Verification
- [ ] `TRACE_ENABLED=0 make test-e2e` completes without errors (no tracing started/stopped)
- [ ] `TRACE_ENABLED=1 make test-e2e` produces trace zips in `artifacts/<run_id>/traces/` on failure
- [ ] Default run (no env var) behaves identically to current (tracing on)

---

## Phase 3: Flow-Level Sleep Optimization

### Overview
Replace the two biggest hard sleeps in flow/component code with condition-based Playwright waits. Overlay sleeps are preserved per design decision.

### Changes Required

#### 1. Checkout page load sleep
**File**: `qa/e2e/netcorner/nuxt/pl/lib/flows/cart_and_checkout_wrappers.py`
**Line**: 145
**Current**: `.wait_loaded().sleep(3_500)`
**Change**: Replace `sleep(3_500)` with a condition-based wait on a checkout section becoming visible.

```python
.wait_loaded()
```

The `wait_loaded()` method already calls `super().wait_loaded()` (waits for `domcontentloaded`) and then `self.content.wait_visible()` + `self.navigation.wait_visible()` (Playwright `expect().to_be_visible()` with 10s timeout). This should be sufficient. If specific checkout content needs additional settling, add an explicit `expect()` on the first interacted component:

```python
checkout = CheckoutPage(self.__page, self.__base_url).wait_loaded()
checkout.content.delivery_type.wait_visible()
```

This replaces a fixed 3.5s sleep with a condition that resolves as soon as the delivery type picker is visible (typically <1s).

#### 2. Listing sorting sleep
**File**: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/listing_components.py`
**Line**: 118
**Current**: `self.sleep(2_000)` after checkbox click
**Change**: Replace with waiting for the listing content to stabilize. The sorting triggers a re-render of product tiles:

```python
# Instead of self.sleep(2_000), wait for listing to re-render
expect(self.root.page.locator("[data-name='listingContent']")).to_be_visible(
    timeout=self.DEFAULT_TIMEOUT
)
```

Or if there is a loading indicator during sort, wait for it to disappear. The exact condition depends on the frontend behavior - investigate the DOM during sort to find the best signal.

### Success Criteria

#### Automated Verification
- [ ] `make test-e2e` passes without regressions
- [ ] `make check` passes

#### Manual Verification
- [ ] Checkout flow completes reliably without the 3.5s fixed wait
- [ ] Sorting flow completes reliably without the 2s fixed wait
- [ ] No flakiness introduced in 3+ consecutive runs

---

## Phase 4: ASO Test Updates & Benchmarking

### Overview
Update existing ASO tests for the modified `BaseComponent` behavior and establish performance benchmarking baseline.

### Changes Required

#### 1. Update existing BaseComponent ASO tests
**File**: `qa/aso/framework/test_base_component_first_visible.py`
**Changes**: The existing tests use `_FakeLocatorItem` and `_FakeLocatorGroup` that implement `count()`, `nth()`, `is_visible()`. These need updating because:

- `_pick_visible` now calls `locator.locator(":visible").first` instead of iterating with `count()`/`nth()`/`is_visible()`
- `find()` no longer calls `first_visible()`
- Action methods now call `locator.locator(":visible").first` instead of `first_visible(locator)`

The fake locator classes need to support `.locator(selector)` method:

```python
class _FakeLocatorItem:
    def __init__(self, *, visible: bool, name: str) -> None:
        self._visible = visible
        self.name = name
        self.click_calls = 0
        self.evaluate_calls = 0
        self.fill_calls: list[str] = []
        self.type_calls: list[str] = []
        self.scroll_calls = 0

    @property
    def first(self) -> _FakeLocatorItem:
        return self

    def count(self) -> int:
        return 1

    def nth(self, _index: int) -> _FakeLocatorItem:
        return self

    def is_visible(self) -> bool:
        return self._visible

    def locator(self, selector: str) -> _FakeLocatorItem:
        """Support chained .locator(':visible').first pattern."""
        return self

    def scroll_into_view_if_needed(self) -> None:
        self.scroll_calls += 1

    def click(self, *, timeout: int) -> None:
        _ = timeout
        self.click_calls += 1

    def evaluate(self, script: str) -> None:
        _ = script
        self.evaluate_calls += 1

    def fill(self, value: str, *, timeout: int) -> None:
        _ = timeout
        self.fill_calls.append(value)

    def type(self, value: str, *, timeout: int) -> None:
        _ = timeout
        self.type_calls.append(value)
```

Similarly `_FakeLocatorGroup` needs `.locator()`:

```python
class _FakeLocatorGroup:
    def __init__(self, items: list[_FakeLocatorItem]) -> None:
        self._items = items
        self._visible_items = [i for i in items if i._visible]

    @property
    def first(self) -> _FakeLocatorItem:
        return self._items[0]

    def count(self) -> int:
        return len(self._items)

    def nth(self, index: int) -> _FakeLocatorItem:
        return self._items[index]

    def locator(self, selector: str) -> _FakeLocatorGroup:
        """Simulate :visible filtering."""
        if ":visible" in selector:
            return _FakeLocatorGroup(self._visible_items if self._visible_items else self._items)
        return self
```

Update test functions to verify new behavior:
- `test_pick_visible_returns_visible_match` - verifies `_pick_visible` returns the visible item
- `test_find_does_not_reresovle_root` - verifies `find()` doesn't trigger visibility check
- `test_pointer_click_uses_visible_filter` - verifies action method uses `:visible` filtering
- `test_wait_visible_resolves_root` - verifies `wait_visible` re-picks the visible root

Rename the test file to `test_base_component.py` since it no longer focuses on `first_visible`.

#### 2. Performance benchmarking
The existing `test_durations.json` infrastructure (`qa/conftest.py:1530-1556`) already captures per-test timing and detects regressions. No new benchmarking code is needed.

After the optimization:
1. Run `make test-e2e` with current code, save `artifacts/<run_id>/test_durations.json` as baseline
2. Apply all changes
3. Run `make test-e2e` again, compare durations
4. The existing regression detection in `pytest_sessionfinish` will log warnings if any test got slower

### Success Criteria

#### Automated Verification
- [ ] `make test-aso` passes with updated/new tests
- [ ] `make check` passes (full pipeline: test-aso → lint → format-check → typecheck → security → verify-discovery → verify-scenarios → collect)
- [ ] `make test-e2e` passes

#### Manual Verification
- [ ] `test_basic_orders` avg time per parametrized case is 60-90s (headless, `HEADLESS=1`)
- [ ] `test_durations.json` shows improvement over baseline
- [ ] No flakiness in 3+ consecutive full E2E runs
- [ ] Tracing artifacts still produced correctly on failure with default settings

---

## Testing Strategy

### Unit Tests (ASO)
- `test_base_component.py` - updated fakes, tests for `_pick_visible`, `find`, action methods, `wait_visible`
- `test_trace_toggle.py` - env var resolution for `TRACE_ENABLED`

### Integration Tests (E2E)
- Full `make test-e2e` run validates all 16 `test_basic_orders` parametrized cases
- Covers all page types: HomePage, ListingPage, ProductPage, CartPage, CheckoutPage
- Covers all delivery types: courier, InPost, DHL POP, storehouse
- Covers auth/anonymous flows

### Manual Testing Steps
1. Run `HEADLESS=1 make test-e2e` and verify all tests pass
2. Run with `TRACE_ENABLED=0` and verify no trace artifacts generated, tests still pass
3. Run with `TRACE_ENABLED=1`, force a test failure, verify trace zip exists in `artifacts/<run_id>/traces/`
4. Compare `test_durations.json` before and after optimization
5. Run 3 consecutive times to verify stability

## Performance Considerations

### Expected Impact
| Optimization | Estimated Savings per Test |
|---|---|
| `find()` stops re-resolving root | 5-30s (eliminates 100-500 protocol calls) |
| `_pick_visible` replaces `first_visible` loop | 2-10s (eliminates O(N) per-component init) |
| `_scope_matches_root` JS eval removed | 1-3s (eliminates 30-80 evaluate() calls) |
| `_resolve_visible_root` polling removed | 0-10s (eliminates worst-case polling) |
| Action method `first_visible` removed | 2-5s (eliminates per-action overhead) |
| Checkout sleep removed | 3.5s fixed |
| Sorting sleep removed | 2s fixed |
| **Total estimated** | **15-60s per test** |

### Risk Factors
1. **`:visible` pseudo-selector edge cases**: If the Nuxt frontend uses CSS `visibility: hidden` instead of `display: none` for mobile elements, the `:visible` filter behavior may differ from `is_visible()`. Need to verify during E2E testing.
2. **Double `:visible` nesting**: Overlay roots already use `:visible` in selectors (e.g., `[data-name="OrderAddressDialog"]:visible`). Nesting `locator(":visible").first` on top should be harmless but needs verification.
3. **Race conditions in `find()`**: Removing root re-resolution from `find()` means if the root element is replaced in the DOM between construction and `find()` calls, the locator chain may break. This is unlikely in practice since components are short-lived.
4. **Sleep removal flakiness**: The 3.5s checkout sleep and 2s sorting sleep may mask real SUT latency. If removing them causes flakiness, add targeted `expect()` conditions rather than reverting to sleeps.

## Migration Notes

This is a big-bang change - no incremental migration needed. All 30 component classes using `resolve_root` continue to work because the `resolve_root` signature and return type are unchanged. The behavioral change is entirely inside `BaseComponent.__init__` and its methods.

### Rollback
If the `:visible` approach fails E2E validation, the previous `first_visible()` implementation can be restored from git. The `resolve_root` simplification (removing `_scope_matches_root`) is independently safe and should be kept even if the `_pick_visible` approach needs adjustment.

## File Change Summary

| File | Change Type | Description |
|---|---|---|
| `framework/base/page_objects/base_component.py` | **Modify** | Replace `first_visible`, `find`, `_resolve_visible_root`, action methods |
| `qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py` | **Modify** | Simplify `resolve_root`, remove `_scope_matches_root` |
| `settings.py` | **Modify** | Add `trace_enabled = True` |
| `framework/env.py` | **Modify** | Add `trace_enabled` to `RuntimeEnv` + `load_env()` |
| `qa/e2e/conftest.py` | **Modify** | Gate tracing on `runtime_env.trace_enabled` |
| `qa/e2e/netcorner/nuxt/pl/lib/flows/cart_and_checkout_wrappers.py` | **Modify** | Remove `sleep(3_500)` |
| `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/listing_components.py` | **Modify** | Replace `sleep(2_000)` with condition wait |
| `qa/aso/framework/test_base_component_first_visible.py` | **Modify** | Rename + update fakes/tests for new behavior |
| `qa/aso/framework/test_trace_toggle.py` | **New** | ASO tests for `TRACE_ENABLED` toggle |

## References

- Original ticket: `thoughts/tickets/debt_e2e_performance_optimization.md`
- Research document: `thoughts/research/2026-04-27_e2e_performance_optimization.md`
- Related: `thoughts/research/2026-04-27_failed_dom_artifacts.md` (artifact lifecycle patterns)
- Framework BaseComponent: `framework/base/page_objects/base_component.py:9-119`
- E2E BaseComponent: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py:8-22`
- Benchmark test: `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py`
- E2E context fixture: `qa/e2e/conftest.py:172-249`
- RuntimeEnv: `framework/env.py:60-153`
