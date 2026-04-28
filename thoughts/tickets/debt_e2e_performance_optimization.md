---
type: debt
priority: high
created: 2026-04-27T15:30:00Z
status: planned
tags: [performance, e2e, optimization, resolve_root, component_architecture]
keywords: [resolve_root, first_visible, BaseComponent, headless, test_basic_orders, xdist, performance]
patterns: [component initialization, locator resolution, visibility checking, test execution, benchmarking]
---

# DEBT-001: E2E Test Performance Optimization - resolve_root and Component Architecture

## Description
E2E tests in headless mode are experiencing severe performance degradation after recent resolve_root changes, with test execution times ranging from 60-360 seconds per test. The target is to optimize performance to achieve 60-90 seconds per test through architectural improvements and removal of unnecessary mobile/desktop complexity.

## Context
Recent changes to resolve_root functionality have introduced significant performance bottlenecks in the qa/e2e/ test suite. The test_basic_orders.py suite specifically shows severe slowdowns in headless mode, while qa/visual/ tests remain unaffected. The current implementation includes unnecessary mobile/desktop dual support that adds complexity without providing value for the E2E test strategy.

## Requirements

### Functional Requirements
- Maintain all existing test scenarios and parametrization in test_basic_orders.py
- Preserve framework modularity and wrapper pattern architecture
- Ensure 100% compatibility with existing E2E test functionality
- Support global optimization across all qa/e2e/ components
- Implement desktop-only locator resolution (eliminate mobile support)

### Non-Functional Requirements
- Target performance: 60-90 seconds per test (currently 60-360 seconds)
- Maintain test reliability and stability
- Support headless execution mode optimization
- Enable performance benchmarking and monitoring
- Optimize xdist parallel execution (currently ineffective beyond 3 workers)

## Current State
- resolve_root method with mobile/desktop complexity causing performance issues
- BaseComponent using expensive first_visible() visibility checks
- _resolve_visible_root() with polling loops creating delays
- Component initialization patterns with redundant locator resolution
- Test execution times of 60-360 seconds per test in headless mode

## Desired State
- Streamlined desktop-only component architecture
- Optimized resolve_root with direct locator resolution
- Performance-optimized BaseComponent with minimal overhead
- Benchmarking system storing performance data in artifacts folder
- Consistent 60-90 second test execution times
- Improved xdist worker efficiency for parallel execution

## Research Context

### Keywords to Search
- resolve_root - Core performance bottleneck method in component initialization
- first_visible - Expensive visibility checking method called extensively
- _resolve_visible_root - Polling loop method causing delays in component resolution
- BaseComponent - Framework base class requiring optimization or replacement
- _scope_matches_root - JavaScript evaluation method potentially causing overhead
- xdist - Parallel test execution system needing optimization analysis
- test_basic_orders - Primary benchmark test file for performance measurement
- ROOT_SELECTOR - Component selector patterns used across E2E components
- headless - Execution mode specifically affected by performance issues

### Patterns to Investigate
- component initialization - How resolve_root is called during component creation
- locator resolution - Current mobile/desktop handling logic and simplification opportunities
- visibility checking - Usage patterns of first_visible and expect() calls for optimization
- test wrapper patterns - Flow analysis of SelectProductWrappers, CartAndCheckoutWrappers, ClientWrappers
- parametrization patterns - Performance impact of auth_session_cases and checkout_delivery_cases
- performance measurement - Benchmarking implementation approaches and artifact storage
- xdist worker patterns - Parallel execution bottlenecks and optimization opportunities

### Key Decisions Made
- Desktop-only approach - Eliminate mobile/desktop dual support complexity
- No backward compatibility - Can break existing mobile handling immediately
- Global E2E scope - Optimize resolve_root across all qa/e2e/ components
- Framework modularity preservation - Maintain wrapper patterns and abstraction layers
- Performance target - 60-90 seconds per test maximum execution time
- Artifacts-based metrics - Store performance data in artifacts folder without CI integration
- New component library - Create optimized E2E components with fallback to cleanup old implementation

## Success Criteria

### Automated Verification
- [ ] All existing test scenarios in test_basic_orders.py pass successfully
- [ ] Performance benchmarks show 60-90 second execution times consistently
- [ ] make test-e2e completes without regressions
- [ ] xdist parallel execution shows improved efficiency beyond 3 workers
- [ ] Component initialization performance metrics stored in artifacts/

### Manual Verification
- [ ] Visual verification that all E2E test functionality remains intact
- [ ] Headless mode execution performs within target timeframes
- [ ] Component locator resolution works correctly for desktop scenarios
- [ ] Test reliability remains stable across multiple execution runs
- [ ] Performance data artifacts are generated and accessible for analysis

## Implementation Strategy

### Phase 1: Analysis and Benchmarking
1. Run performance profiling on current resolve_root implementation
2. Identify specific bottlenecks in component initialization chain
3. Establish baseline performance metrics for test_basic_orders.py
4. Analyze xdist worker utilization and bottlenecks

### Phase 2: Core Optimization
1. Implement desktop-only resolve_root with direct locator resolution
2. Optimize BaseComponent first_visible() method or create E2E-specific alternative
3. Eliminate _resolve_visible_root() polling loops where possible
4. Streamline component initialization patterns

### Phase 3: Architecture Refactoring
1. Create performance-optimized E2E component library
2. Implement component-level locator caching if needed
3. Optimize test fixture usage and browser context management
4. Simplify redundant expect() and visibility checks

### Phase 4: Validation and Cleanup
1. Comprehensive testing of optimized implementation
2. Performance verification against 60-90 second target
3. Remove old mobile/desktop complexity after successful migration
4. Document performance optimization patterns for future use

## Related Information
- Recent commits: d0cf834, 2b2e695, ca797ba, 313cb65 (resolve_root changes)
- Target test file: qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py
- Framework base: framework/base/page_objects/base_component.py
- E2E base: qa/e2e/netcorner/nuxt/pl/lib/page_objects/base_component.py

## Notes
- Visual tests (qa/visual/) do not show similar performance degradation
- Current implementation described as "przekombinowane i nasrane" - overly complex
- xdist effectiveness drops significantly beyond 3 workers
- Performance data should be stored in artifacts folder without CI integration requirements
- Framework modularity and wrapper patterns must be preserved - avoid direct Playwright API rewrites
- Test result caching explicitly excluded from scope