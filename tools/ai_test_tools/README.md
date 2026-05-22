# AI Test Tools

Tools for collecting user-flow artifacts and preparing new automated E2E tests without hardcoding environment hosts.

## What this package provides

- `manual_trace_recorder.py` - manual Playwright trace recorder with checkpoint capture.
- `examples/checkpoints.sample.json` - example checkpoint schema.
- `skills/new-test-prepare/SKILL.md` - agentic pre-prompt skill for scenario preparation.
- `skills/new-test-generate/SKILL.md` - follow-up skill for generating test code from prepared payload.
- `skills/new-test-suite-prepare/SKILL.md` - research/planning for multi-scenario suite from many recordings.
- `skills/new-test-suite-generate/SKILL.md` - multi-scenario suite generator from many recording sets.
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
4. `/new_test_prepare` writes deterministic payload file to `thoughts/ai_gen/prepared/*.json`
5. Use `generation_payload_path` from step 4 in `/new_test_generate`
6. During generation, confirm with user: test name, markers, severity, and target file strategy.

### Deterministic research output contract

Research commands always produce fixed-order output and save a payload file for handoff:

- single test flow:
  - command: `/new_test_prepare`
  - payload: `generation_payload`
  - output file: `thoughts/ai_gen/prepared/<timestamp>_<scenario>_generation_payload.json`
- multi-scenario suite flow:
  - command: `/new_test_suite_prepare`
  - payload: `suite_generation_payload`
  - output file: `thoughts/ai_gen/prepared/<timestamp>_<suite>_suite_generation_payload.json`

## Build suite from many recordings

If you already have multiple recording runs and want one coherent suite (shared architecture + builders + parametrization):

1. Prepare a `recording_sets` list where each entry contains:
   - `scenario_name`
   - `trace_zip_path`
   - `checkpoints_json_path`
   - optional `metadata_json_path`
2. Run `/new_test_suite_prepare` with:
   - `suite_name`
   - `target_domain`
   - `recording_sets`
3. Save and copy `suite_generation_payload_path` from prepare output.
4. Run `/new_test_suite_generate` using `suite_generation_payload_path`.
5. During generation, confirm with user: suite name, markers, severity policy, and file strategy.
5. Expected generator behavior:
   - one consistent suite architecture across scenarios,
   - stable case objects (`case_id`) and parametrization,
   - shared test data builders where practical,
   - explicit business assertions in tests only.

## URL policy

- Do not hardcode hosts/domains in generated plans/tests.
- Use runtime-provided base URL and path semantics.
- Paths/endpoints can be used as hints, but keep solutions portable across test environments.

## OpenCode token optimization

Repository-level OpenCode plugins can reduce repeated repository scanning cost:

- `.opencode/plugins/repo-context-cache.js` builds and refreshes compact map file:
  - `repo_map.json` (repository root)
- The plugin injects compact repo context into chat system prompt, so commands do less broad rediscovery.

After changing `opencode.json` or `.opencode/plugins/*`, restart OpenCode to load updates.
