# AI Test Tools

Tools for collecting user-flow artifacts and preparing new automated E2E tests without hardcoding environment hosts.

## What this package provides

- `manual_trace_recorder.py` - manual Playwright trace recorder with checkpoint capture.
- `examples/checkpoints.sample.json` - example checkpoint schema.
- `skills/new-test-prepare/SKILL.md` - agentic pre-prompt skill for scenario preparation.
- `skills/new-test-generate/SKILL.md` - follow-up skill for generating test code from prepared payload.
- `opencode.snippets.md` - snippets for registering commands/skills in `opencode.json`.

## Why this flow

- No pre-existing automated test is required.
- Start URL is provided manually (`--start-url`) for every run.
- Host/domain is intentionally not fixed in scripts/prompts.
- Analysis is route/path-aware and environment-agnostic.

## Prerequisites

From repository root:

```bash
python -m pip install -e ".[dev]"
```

Install Playwright browser once (if missing):

```bash
.venv/bin/python -m playwright install chromium
```

## Record a new flow

Run from repository root:

```bash
.venv/bin/python tools/ai_test_tools/manual_trace_recorder.py \
  --start-url "https://example.test.netcorner.pl/" \
  --scenario-name "guest_checkout_happy_path" \
  --target-domain "nuxt"
```

Show CLI help:

```bash
.venv/bin/python tools/ai_test_tools/manual_trace_recorder.py --help
```

The help output includes:

- all arguments and defaults
- copy-paste usage examples
- interactive command reference used during recording

During the session:

- `c` - capture checkpoint (assertion intent + screenshot; optional explicit element bind)
- `u` - undo last checkpoint (also removes its screenshot)
- `e` - edit last checkpoint fields (label/expectation/strategy/hint/etc.)
- `s` - save and stop
- `h` - help
- `q` - abort session and save current artifacts

### Explicit element binding for assertions

When you press `c`, recorder asks: `bind to concrete page element? [y/N]`.

- choose `y`
- click one exact element in the browser
- press Enter in terminal

Recorder stores `element` metadata inside checkpoint with selector candidates, for example:

- `data-testid`/`data-test`/`data-qa` selectors when available
- `id` selector when present
- attribute selectors (`aria-label`, `name`)
- short CSS path fallback

This gives `/new_test_prepare` an unambiguous page anchor and reduces descriptive-only checkpoints.

### Dynamic selection hints (recommended)

Each checkpoint also supports:

- `automation_hint` - free-text note for generator, e.g. `pick first product with promo badge and price below 200`.
- `selection_strategy` - `exact` or `dynamic`.

Use `dynamic` when clicked element may disappear in future data snapshots. This helps `/new_test_prepare` convert your action into robust test logic (filter/choose by stable traits instead of hardcoded one item).

Window behavior:

- Default mode uses resizable browser window (`no_viewport=True`) so you can resize freely.
- If you need fixed viewport behavior, add `--fixed-viewport`.

## Output artifacts

The recorder creates:

- `artifacts/manual-traces/<timestamp>_<scenario>/trace.zip`
- `artifacts/manual-traces/<timestamp>_<scenario>/checkpoints.json`
- `artifacts/manual-traces/<timestamp>_<scenario>/metadata.json`
- `artifacts/manual-traces/<timestamp>_<scenario>/screenshots/*.png`

## Checkpoint authoring guidance

Use 4-8 checkpoints per scenario:

1. Entry state ready (first stable screen)
2. Key business action completed
3. Intermediate state change (toast/panel/status)
4. Final business outcome

Naming tips:

- Stable IDs only: `cart_contains_added_product`
- Avoid environment-specific host references
- Keep expectation text business-readable

## Flow into new-test commands

1. Record with `manual_trace_recorder.py`
2. Open trace locally:

```bash
npx playwright show-trace "artifacts/manual-traces/<run>/trace.zip"
```

3. Feed `trace.zip + checkpoints.json + metadata.json` into `/new_test_prepare`
4. Use generated payload in `/new_test_generate`

## URL policy

- Do not hardcode hosts/domains in generated plans/tests.
- Use runtime-provided base URL and path semantics.
- Paths/endpoints can be used as hints, but keep solutions portable across test environments.
