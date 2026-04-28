---
date: 2026-04-27T18:49:56+02:00
git_commit: f9d38d887887346c891e93f79b771fdab48cfda3
branch: feature/NN-24005-tech-zapisywanie-dom-dla-testow-ktore-nie-przechodza-pod-analize-ai
repository: qa-test-netquarner
topic: "DEBT-001: E2E Test Performance Optimization - resolve_root and Component Architecture"
tags: [research, codebase, performance, e2e, resolve_root, BaseComponent, xdist, component_architecture]
last_updated: 2026-04-27
---

## Ticket Synopsis

E2E tests in headless mode experience severe performance degradation (60-360s per test) after recent `resolve_root` changes. The target is 60-90s per test through: desktop-only locator resolution, optimized `BaseComponent`, elimination of polling loops, and improved xdist parallel efficiency. Framework modularity and wrapper patterns must be preserved.

## Summary

The performance bottleneck is a compound effect of three interacting layers:

1. **Component initialization overhead**: Every component creation triggers `resolve_root` → `first_visible()` which iterates DOM elements calling `is_visible()` on each. With 35-80 components created per test and `find()` re-running `first_visible` on every call, this produces hundreds of Playwright protocol round-trips per test.

2. **Polling loops and fixed waits**: `_resolve_visible_root()` polls every 100ms calling `first_visible` each iteration. Combined with explicit `sleep()` calls in flow wrappers (3.5s checkout wait, 2s sorting wait, 1-1.5s overlay waits), there is a hard lower bound of ~10-15s in fixed waits per test.

3. **xdist scaling limits**: Workers are independent (separate browsers), but scaling beyond ~3 workers is limited by: shared SUT throughput, per-test tracing/video overhead, small test pool (16 cases), and per-test artifact/reporting teardown I/O.

## Detailed Findings

### resolve_root Initialization Chain

The hot path for every component creation is:

```
Component.__init__()
  → resolve_root(scope, ROOT_SELECTOR)        # E2E BaseComponent
    → _scope_matches_root(scope, selector)     # JS evaluate() if scope is Locator
    → scope.locator(selector)                  # Playwright locator creation
  → FrameworkBaseComponent.__init__(root)
    → first_visible(root)                      # Iterates ALL matches checking visibility
      → locator.count()                        # 1 protocol call
      → nth(i).is_visible()                    # 1 protocol call per candidate
```

- **30 of 33 component classes** use `resolve_root` in their constructors (`base_component.py:14`)
- When `scope` is a `Locator` (common in section/page compositions), `_scope_matches_root` adds a `scope.evaluate()` JS round-trip (`base_component.py:10-11`)
- Best case per init: 2-3 protocol calls; worst case with M matches: 2+M calls

**Key file**: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py:8-19`
**Key file**: `framework/base/page_objects/base_component.py:9-32`

### first_visible() - The Core Bottleneck

```python
@staticmethod
def first_visible(locator: Locator) -> Locator:
    count = locator.count()           # Protocol call
    for index in range(count):
        candidate = locator.nth(index)
        if candidate.is_visible():    # Protocol call per candidate
            return candidate
    return locator.first
```

This is called:
- Once in every component constructor (`base_component.py:14`)
- Again on every `find()` call (`base_component.py:91-93`) - this is the major amplifier
- Again in `_resolve_visible_root` polling loop (`base_component.py:95-113`)
- Again in `pointer_click`, `non_pointer_click`, `safe_fill`, `safe_type` (`base_component.py:53-85`)

Components with many `find()` calls in constructors multiply the cost:
- `CartProductComponent`: 10 `find()` calls (`cart_components.py:36-45`)
- `RegisterClientComponent`: many `find()` calls (`register_client_component.py:17-47`)
- `MyAccountComponent`: many `find()` calls (`my_account_component.py:18-33`)

**Key file**: `framework/base/page_objects/base_component.py:18-32, 91-93`

### _resolve_visible_root() Polling Loop

```python
def _resolve_visible_root(self, *, timeout: int) -> Locator:
    self.root = self.first_visible(self._root_candidates)
    if self.root.is_visible(): return self.root
    deadline = time.monotonic() + (timeout / 1000)
    while time.monotonic() < deadline:
        self.root = self.first_visible(self._root_candidates)  # Full re-scan
        if self.root.is_visible(): return self.root
        time.sleep(0.1)  # 100ms poll interval
    return self.root
```

- Called by `wait_visible()` and `assert_visible()` which are used in every page's `wait_loaded()` chain
- Worst case near timeout (10s default): ~100 iterations, each running full `first_visible`
- Pages call `wait_loaded()` in chains: `HomePage`, `ListingPage`, `ProductPage`, `CartPage`, `CheckoutPage` each wait 3-5 section components

**Key file**: `framework/base/page_objects/base_component.py:95-113`

### _scope_matches_root() - JS Evaluation Overhead

```python
@staticmethod
def _scope_matches_root(scope: Locator, root_selector: str) -> bool:
    return bool(scope.evaluate(
        "(node, selector) => node instanceof Element && node.matches(selector)",
        root_selector
    ))
```

- Executes browser-side JS via Playwright protocol for every component where scope is a Locator
- Not mobile/desktop detection per se, but supports "re-scoping" optimization (avoid double-nesting locators)
- Computationally trivial JS but latency-bound due to protocol round-trip

**Key file**: `qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py:10-11`

### Component Count Per Test Execution

For a single `test_basic_orders` test case:

| Flow Phase | Components Created | Notes |
|---|---|---|
| `_prepare_client_session` (authenticated) | ~20-30 | HomePage, RegisterPage, MyAccountPage + all section/overlay components |
| `SelectProductWrappers.select_test_product` | ~15+ k tiles | ListingPage + content/sorting/filter components + ProductPage + overlays |
| `CartAndCheckoutWrappers.process_cart` | ~5+ m items | CartPage + CartProductComponent per item |
| `CartAndCheckoutWrappers.process_checkout` | ~12-17 | CheckoutPage + delivery/purchaser/payment/summary components + overlays |
| **Total (unauthenticated)** | **~35-50** | |
| **Total (authenticated)** | **~55-80** | |

Each component init triggers `first_visible`, and many trigger additional `find()` calls, compounding to hundreds of protocol round-trips.

### Test Parametrization Impact

`test_basic_orders` is double-parametrized:
- `auth_session_cases()`: 2 cases (logged_in, anonymous) - `client_generators.py:81-85`
- `checkout_delivery_cases()`: 8 cases (4 delivery types x 2 person types) - `checkouts_generators.py:373-431`
- **Total: 16 independent test nodes**

Each case generates unique data (UUID-based emails), so there are no data dependencies preventing parallel execution.

**Key file**: `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py:21-22`

### Fixed Waits in Flow Code

Hard lower bounds per test from explicit sleeps/polls:
- Checkout page load wait: 3.5s (`cart_and_checkout_wrappers.py:145`)
- Delivery provider stability polling: up to 2.5s (`cart_and_checkout_wrappers.py:93-131`)
- Purchaser overlay waits: 1-1.5s + poll (`purchaser_overlay.py:47,51,75,83`)
- Courier overlay: 1.5s (`courier_receiver_overlay.py:75`)
- Listing sorting checkbox: 2s (`listing_components.py:118`)
- Storehouse overlay settle/poll: variable (`delivery_storehouse_receiver_overlay.py:20-22,67,74`)
- Delivery component polling: variable (`delivery_type_component.py:87-105`)

**Estimated fixed wait floor: ~10-15s per test** (varies by delivery type).

### xdist Parallel Execution Analysis

**Configuration:**
- `Makefile` runs `pytest -m e2e -q` with no `-n` flag (`Makefile:35-37`)
- Worker count is manually specified via CLI
- Each worker gets its own browser process (`qa/e2e/conftest.py:162-169`)
- Workers share artifacts root: `artifacts/<run_id>/` (`framework/artifacts.py:52-65`)

**Why scaling drops after ~3 workers:**

1. **Shared SUT throughput**: All workers hit the same `server_name` host (`settings_cli.py:11`). Backend throughput (DB, session, search, checkout endpoints) becomes the bottleneck.

2. **Per-test fixed overhead**: Each test creates a new browser context with tracing (`screenshots=True, snapshots=True, sources=True`) and optionally video (`qa/e2e/conftest.py:184-189`). This is a high per-test CPU/IO tax that scales with worker count.

3. **Small test pool**: With only 16 test cases, per-worker startup/browser launch cost is amortized over fewer tests as workers increase.

4. **Per-test teardown I/O**: Every test writes step artifacts JSON, persists worker payloads, and sends reporting events (`qa/conftest.py:1621-1723`).

5. **No grid**: `is_grid_available = False` means all browser processes run on the same machine, competing for CPU/RAM.

**Key files**: `qa/e2e/conftest.py:154-249`, `qa/conftest.py:60-81,1530-1556`, `settings_cli.py:14`

### Mobile/Desktop Complexity

The ticket's reference to "mobile/desktop dual support" maps to:
- `_scope_matches_root` JS evaluation in `resolve_root` (scope re-use optimization, not viewport detection)
- Dual CSS selectors in some components: `[data-name="cartFooter"], [data-name="stickyBar"]` (`footer_component.py:17`), `[data-name='orderParcelPicker'], [data-name='OrderReceiverPicker']` (`delivery_object_component.py:10`)
- VIEWPORT_PRESETS including "mobile" preset (`qa/e2e/conftest.py:27-28`)
- `filtersDesktop` naming in listing selectors (`listing_components.py:19`)

The actual `resolve_root` does **not** branch on viewport/device. The "mobile/desktop" complexity is in **selector design** (compound selectors matching both layouts) rather than runtime branching logic.

## Code References

### Core Performance Chain
- `framework/base/page_objects/base_component.py:9-119` - Framework BaseComponent with first_visible, _resolve_visible_root, find
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py:8-19` - E2E BaseComponent with resolve_root, _scope_matches_root

### Component Examples (30 classes use resolve_root)
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/cart_components.py:30-45` - CartProductComponent with 10 find() calls
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/listing_components.py:78-86` - ListingSortingComponent
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/checkout/delivery_type_component.py:21-28` - CheckoutDeliveryTypeComponent

### Test and Wrappers
- `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py:1-64` - Benchmark test file
- `qa/e2e/netcorner/nuxt/pl/lib/flows/select_product_wrappers.py:25-89` - Product selection flow
- `qa/e2e/netcorner/nuxt/pl/lib/flows/cart_and_checkout_wrappers.py:45-300` - Cart and checkout flow
- `qa/e2e/netcorner/nuxt/pl/lib/flows/client_wrappers.py:11-55` - Client registration flow

### Parametrization
- `qa/e2e/netcorner/nuxt/pl/lib/test_data/client/client_generators.py:81-85` - auth_session_cases (2 cases)
- `qa/e2e/netcorner/nuxt/pl/lib/test_data/checkout/checkouts_generators.py:373-431` - checkout_delivery_cases (8 cases)

### Configuration and Infrastructure
- `pytest.ini:1-26` - Test configuration (no xdist default)
- `settings_cli.py:1-14` - Runtime defaults (headless=True, grid=False)
- `framework/env.py:60-77,193,232` - RuntimeEnv dataclass and headless resolution
- `qa/e2e/conftest.py:154-249` - Browser/context/page fixture lifecycle
- `qa/conftest.py:60-81,1530-1556,1590-1616` - xdist checks, timing hooks

### Flow Sleep/Wait Locations
- `qa/e2e/netcorner/nuxt/pl/lib/flows/cart_and_checkout_wrappers.py:145` - 3.5s checkout sleep
- `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/listing_components.py:118` - 2s sorting sleep

## Architecture Insights

### Performance Bottleneck Architecture (Root Cause Chain)

```
test_basic_orders (16 parametrized cases)
  └─ Each test creates 35-80 components
       └─ Each component calls resolve_root → first_visible
            └─ first_visible iterates DOM elements (O(M) protocol calls)
                 └─ find() re-runs first_visible on every sub-locator access
                      └─ Components with N find() calls = N × first_visible
                           └─ _resolve_visible_root polls every 100ms, each calling first_visible
```

**Estimated per-test protocol calls**: 500-2000+ Playwright round-trips (depends on component count, DOM match counts, and polling iterations).

### Optimization Opportunities (Priority Order)

1. **Eliminate `first_visible` from `find()`** - `find()` re-resolves root on every call (`base_component.py:91-93`). This is the highest-frequency bottleneck. Consider caching the resolved root.

2. **Replace `first_visible` with direct `.first` locator** - For desktop-only E2E, visibility iteration is unnecessary if selectors are specific enough. Use `locator.first` directly.

3. **Remove `_scope_matches_root` JS eval** - The `evaluate()` call adds a round-trip per Locator-scoped component. If desktop-only selectors are unique, this optimization is unnecessary.

4. **Replace `_resolve_visible_root` polling with Playwright auto-waiting** - Playwright's `expect().to_be_visible()` already handles waiting. The manual polling loop duplicates this with worse performance.

5. **Reduce fixed sleeps in flow code** - Replace `sleep(3500)` with condition-based waits using Playwright's auto-waiting capabilities.

6. **Optimize tracing configuration** - Consider disabling `sources=True` in tracing or making tracing opt-in for performance runs.

7. **xdist**: Use Selenium Grid or remote browsers to distribute browser CPU load; increase test pool to amortize per-worker startup.

### Design Constraints
- Wrapper pattern architecture must be preserved
- All existing test scenarios must continue to pass
- No backward compatibility needed for mobile handling
- New optimized component library approach is approved (build new, migrate, clean up old)

## Historical Context (from thoughts/)

- `thoughts/tickets/debt_e2e_performance_optimization.md` - The source ticket documenting the performance regression, target metrics (60-90s/test), and phased implementation strategy. Key decisions: desktop-only approach, no backward compatibility for mobile, global E2E scope, artifacts-based benchmarking.
- `thoughts/tickets/feature_failed_dom_artifacts.md` - Related feature for DOM snapshots on failure; failure-only capture design ensures no steady-state performance impact.
- `thoughts/research/2026-04-27_failed_dom_artifacts.md` - Research documenting framework lifecycle patterns, xdist artifact mechanics, and the `_artifacts_payload` publication pattern.
- `thoughts/plans/failed_dom_artifacts_implementation_plan.md` - Implementation plan reinforcing failure-only artifact patterns and deterministic naming.
- `thoughts/reviews/failed_dom_artifacts_implementation-review.md` - Confirms failed-dom artifacts are fully implemented with minimal performance impact.

Key historical insight: The failed-DOM artifact work documents the framework's lifecycle patterns (fixture teardown, xdist-safe naming, artifact publication) that should be reused for any performance benchmarking instrumentation.

## Related Research

- `thoughts/research/2026-04-27_failed_dom_artifacts.md` - Framework lifecycle and artifact patterns applicable to performance instrumentation

## Open Questions

1. **Exact protocol call count**: What is the precise number of Playwright protocol round-trips per test case? A profiling run with protocol logging would give definitive numbers.

2. **DOM match counts**: How many DOM elements match common ROOT_SELECTOR patterns like `[data-name='cartProduct']`? High match counts in `first_visible` loops would explain worst-case performance.

3. **Headless vs headed performance delta**: The ticket notes headless-specific degradation. Is this due to different rendering/visibility behavior in headless Chromium affecting `is_visible()` results?

4. **SUT throughput ceiling**: What is the target server's actual concurrent request capacity? This determines the xdist worker ceiling regardless of client-side optimizations.

5. **Tracing overhead quantification**: How much time does `context.tracing.start(screenshots=True, snapshots=True, sources=True)` add per test? This could be a significant constant factor.

6. **`find()` call frequency at runtime**: Beyond constructor `find()` calls, how many runtime `find()` calls occur during typical test actions (clicking, filling, asserting)? Each one re-runs `first_visible`.
