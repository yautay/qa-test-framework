# Central plugin model (aQuArius)

Plugins in aQuArius should extend analytics and policy behavior without changing core ingestion.

## Plugin categories

- `enrichment`
  - enrich events with derived fields (suite, team, area).
- `analytics`
  - flaky scoring,
  - duration trends,
  - failure clustering.
- `policy`
  - release gate decisions,
  - SLA checks,
  - mandatory test set checks.
- `notifications`
  - Slack/Teams/email alerts.

## Suggested plugin interface

- `name: str`
- `enabled(config) -> bool`
- `on_event(event, context) -> None`
- `on_run_closed(run, context) -> None`
- `healthcheck() -> dict`

## Execution policy

- Ingestion core must stay deterministic and stable.
- Plugin failures should not drop accepted events.
- Plugin failures should emit warnings and health metrics.

## Recommended first plugins

1. `run_summary_plugin`
   - computes final counters and run duration checks.
2. `flaky_detection_plugin`
   - marks flaky by retry/pass pattern and historical instability.
3. `slow_regression_plugin`
   - detects p95 duration regressions.
4. `quality_gate_plugin`
   - computes pass/fail for `pr/nightly/release` policies.
5. `visual_threshold_recommendation_plugin`
   - computes trend-based threshold suggestions for visual regression,
   - scope key: `scenario_id + viewport + browser_family`,
   - minimum sample gate: 20 runs,
   - suggestion guardrail: max +20% increase per update.
