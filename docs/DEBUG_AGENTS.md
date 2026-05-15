# DEBUG_AGENTS.md — Debugging Guide for AI Agents

This file describes how to diagnose failing E2E tests in this repository.
When a test fails, follow this guide before touching any code.

---

## 1. Locate the Artifact Run Directory

All run artifacts live under `artifacts/<run_id>/` at the repo root.

The most recent failing run is typically the directory with the latest timestamp name
(`YYYYMMDD_HHMMSS_microseconds`). Find it:

```bash
ls -lt artifacts/ | head -5
```

A complete run directory has:

```
artifacts/<run_id>/
  logs/              # Structured JSON logs per worker + controller
  screenshots/       # Full-page PNG screenshots on failure (raw + annotated)
  traces/            # Playwright trace zips per failed test
  failed-dom/        # Full page.content() HTML snapshot on failure
  allure-results/    # Allure JSON result files (if ALLURE_ENABLED)
  workers/           # Per-worker step traces (steps/<nodeid>.steps.json)
  run-metadata.json  # Run-level metadata (tester, run_note, git info)
```

---

## 2. Read the Logs First

Logs are structured JSON (one JSON object per line). The fastest way to find errors:

```bash
# Find all ERROR-level entries across all workers
python3 -c "
import json, os, glob
for f in glob.glob('artifacts/<run_id>/logs/*.log'):
    for line in open(f):
        try:
            d = json.loads(line)
            if d.get('record',{}).get('level',{}).get('name') == 'ERROR':
                print(d['text'][:300])
        except: pass
"
```

Key fields in each log entry:
- `text` — the formatted log message
- `record.extra.nodeid` — which test was running (`(session)` = between tests)
- `record.extra.worker_id` — which xdist worker
- `record.extra.status` — `failed` / `passed` / `unknown` (on teardown entries)
- `record.level.name` — `INFO`, `WARNING`, `ERROR`

Errors emitted by test code have a `TEST_ERROR code=...` prefix for easy grep:

```bash
grep "TEST_ERROR" artifacts/<run_id>/logs/*.log
```

---

## 3. Read the Failed DOM Snapshot

When a browser test fails, the framework automatically captures `page.content()` at the
moment of failure as `failed-dom/<nodeid>.html`.

**The DOM snapshot corresponds to the page state at test teardown, not the exact moment
of the assertion.** For timing-sensitive failures (e.g. UI flickering) the DOM may look
"correct" by the time it is captured.

Useful things to inspect in the DOM:

```bash
# List all data-name attributes present (tells you what components rendered)
python3 -c "
import re
with open('artifacts/<run_id>/failed-dom/<nodeid>.html') as f:
    content = f.read()
print(sorted(set(re.findall(r'data-name=\"([^\"]+)\"', content))))
"

# Check selected state of delivery tiles (example pattern)
python3 -c "
import re
with open('artifacts/<run_id>/failed-dom/<nodeid>.html') as f:
    content = f.read()
for m in re.finditer(r'data-provider=\"([^\"]+)\".*?border-blue-clear', content, re.DOTALL):
    print('selected provider:', m.group(1))
"
```

---

## 4. Read the Screenshots

Screenshots are written as `screenshots/<nodeid>_raw.png` and `<nodeid>_annotated.png`.

Read them directly in the agent using the `Read` tool — they are images and will be
returned as attachments. Screenshots are taken at teardown so they show the final UI
state, not the intermediate state that caused the failure.

---

## 5. Inspect the Playwright Trace

Traces are stored as zip archives: `traces/<nodeid>.zip`.

Extract and parse `trace.trace` (newline-delimited JSON) to reconstruct exact call
sequences and return values:

```bash
mkdir /tmp/trace_debug
unzip "artifacts/<run_id>/traces/<nodeid>.zip" -d /tmp/trace_debug

python3 -c "
import json
with open('/tmp/trace_debug/trace.trace') as f:
    events = [json.loads(l) for l in f if l.strip()]

# Print all before/after call pairs with selector and result
for e in events:
    t = e.get('type','')
    cid = e.get('callId','')
    if t == 'before':
        method = e.get('method','')
        sel = (e.get('params') or {}).get('selector','')[:80]
        print(f'{cid} CALL  {method} {sel}')
    elif t == 'after':
        val = (e.get('result') or {}).get('value')
        if val is not None:
            print(f'{cid} RESULT {val}')
"
```

**The trace is the ground truth for what Playwright actually observed.** It is
especially useful for:
- Locator `is_visible()` return values over time (detecting flicker/flap)
- `getAttribute` results showing which DOM attribute value was read
- Click coordinates and timing
- Whether a `waitForTimeout` was reached

Trace `startTime` / `endTime` are monotonic ms counters, not wall-clock timestamps.
To find calls near a specific error, search logs for the error timestamp and correlate
with `record.elapsed.seconds`.

---

## 6. Inspect Step Traces

Per-test step execution is recorded in `workers/<worker_id>/steps/<nodeid>.steps.json`.
These are high-level `@step(...)` and `with step_context(...)` traces, useful for
understanding which business-level step the test was executing when it failed.

---

## 7. Allure Result Details

`allure-results/<uuid>-result.json` contains:
- `status` — `passed`, `failed`, `broken`, `skipped`
- `statusDetails.message` — the AssertionError message
- `parameters` — parametrize values (delivery_case, auth_case, etc.)
- `fullName` — the full test qualified name

To find all failures with their messages:

```bash
python3 -c "
import json, os
for f in os.listdir('artifacts/<run_id>/allure-results'):
    if not f.endswith('.json') or 'result' not in f:
        continue
    try:
        d = json.load(open(f'artifacts/<run_id>/allure-results/{f}'))
        if d.get('status') == 'failed':
            params = {p['name']:p['value'] for p in d.get('parameters',[])}
            msg = d.get('statusDetails',{}).get('message','')[:150]
            print(d.get('fullName',''), params.get('delivery_case',''), '|', msg)
    except: pass
"
```

---

## 8. Debugging Checkout / Delivery UI Issues

The checkout delivery section has known sensitivity to AJAX re-renders.

When `DELIVERY_PROVIDER_UNREADABLE_AFTER_PICKUP` or `DELIVERY_TYPE_CHANGED_AFTER_PICKUP`
appears in logs, **the trace is mandatory** — the DOM snapshot will often look correct
because the UI stabilized before teardown.

Pattern to extract per-call `isVisible` and `getAttribute` results from the trace:

```bash
python3 -c "
import json
with open('/tmp/trace_debug/trace.trace') as f:
    events = [json.loads(l) for l in f if l.strip()]

calls = {}
for e in events:
    cid = e.get('callId','')
    t = e.get('type','')
    if t == 'before' and cid:
        calls[cid] = {'method': e.get('method',''), 'sel': (e.get('params') or {}).get('selector','')[:60]}
    elif t == 'after' and cid and cid in calls:
        val = (e.get('result') or {}).get('value')
        m = calls[cid]['method']
        if m in ('isVisible', 'getAttribute', 'queryCount'):
            print(f'{cid:20s} {m:20s} val={val}  sel={calls[cid][\"sel\"][-50:]}')
"
```

Key things to look for:
- `isVisible` flapping between `True`/`False` on the same element across loop iterations
  → the icon/indicator is being re-rendered by AJAX (do not use `is_visible()` alone as
    the selection signal; use a stable DOM attribute instead, e.g. `border-blue-clear`
    class on the tile `<article>` element)
- `getAttribute` returning unexpected provider name
  → check if multiple elements match the selector

---

## 9. Determining DOM Structure Changes

When a locator stops working after a frontend deployment, compare:

1. The selector in the page object (`ROOT_SELECTOR`, `self.find(...)`, etc.)
2. The `data-name` / `data-provider` / `data-picker` attributes actually present in
   the failed DOM snapshot

```bash
# All data-* attributes in the failed DOM
python3 -c "
import re
content = open('artifacts/<run_id>/failed-dom/<nodeid>.html').read()
attrs = set(re.findall(r'(data-[a-z-]+)=\"[^\"]+\"', content))
print(sorted(attrs))
"
```

The checkout page uses `data-picker` on section wrappers and `data-name` / `data-provider`
on individual tiles. If a section is missing entirely from the DOM snapshot, it may have
been collapsed/hidden by the step progression (e.g. a completed checkout substep may
render collapsed).

---

## 10. Connectivity and Environment Sanity

Before concluding a test failure is a code bug, verify the environment is reachable:

```bash
curl -skL -o /dev/null -w "%{http_code}" https://komputronik-galak.test.netcorner.pl/
curl -skL -o /dev/null -w "%{http_code}" https://admin-galak.test.netcorner.pl/admin.php
```

Expected: `200` or `302`. Anything else means VPN is down or the environment is
unhealthy — do not start debugging test code until connectivity is confirmed.

Check `run-metadata.json` for the `environment_probe` block which captures the HTTP
status the test runner saw at startup:

```bash
python3 -c "
import json
d = json.load(open('artifacts/<run_id>/run-metadata.json'))
print(d.get('environment_probe', {}))
"
```

---

## 11. Common Error Codes in Logs

| `TEST_ERROR code` | Meaning | Where to look |
|---|---|---|
| `DELIVERY_PROVIDER_UNREADABLE_AFTER_PICKUP` | `get_selected_delivery_provider` timed out in stability loop | Trace: isVisible flapping on `tileSelectIndicator` |
| `DELIVERY_TYPE_CHANGED_AFTER_PICKUP` | Provider changed immediately after modal close | Trace: first `getAttribute` result |
| `DELIVERY_PROVIDER_DRIFT_AFTER_PICKUP` | Provider changed during stability window | Trace: getAttribute oscillates |

---

## 12. File Locations Quick Reference

| What | Path |
|---|---|
| Structured logs | `artifacts/<run_id>/logs/run_<run_id>_<gw>.log` |
| Controller log | `artifacts/<run_id>/logs/run_<run_id>_master.log` |
| Playwright traces | `artifacts/<run_id>/traces/<nodeid>.zip` |
| Failed DOM snapshots | `artifacts/<run_id>/failed-dom/<nodeid>.html` |
| Screenshots (raw) | `artifacts/<run_id>/screenshots/<nodeid>_raw.png` |
| Screenshots (annotated) | `artifacts/<run_id>/screenshots/<nodeid>_annotated.png` |
| Allure results | `artifacts/<run_id>/allure-results/*.json` |
| Step traces | `artifacts/<run_id>/workers/<gw>/steps/<nodeid>.steps.json` |
| Run metadata | `artifacts/<run_id>/run-metadata.json` |
| Checkout delivery component | `qa/e2e/netcorner/nuxt/pl/lib/page_objects/components/checkout/delivery_type_component.py` |
| Checkout wrapper (stability logic) | `qa/e2e/netcorner/nuxt/pl/lib/flows/cart_and_checkout_wrappers.py` |
