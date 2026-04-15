# OpenCode Commands For E2E

This directory stores versioned OpenCode assets so developers do not need to handcraft prompts.

Goals:

- focus on E2E test generation,
- POM in the `page.section.component.method` scheme,
- reuse of existing flows/wrappers (especially `qa/e2e/netcorner/nuxt/pl/lib/flows/client_wrappers.py`),
- minimal extensions only, without "just in case" Page Objects.

## What is in this directory

- `tools/opencode/commands/` - OpenCode commands (Markdown),
- `tools/opencode/opencode.agents.json` - optional agent profiles,
- `tools/opencode/register_project_commands.py` - registration helper for `.opencode/commands`,
- `tools/opencode/cache_dom_snapshot.py` - DOM snapshot + cache helper,
- `tools/opencode/job_init.py` - initialize versioned job workspace,
- `tools/opencode/job_analyze.py` - exploratory analysis pass for a job,
- `tools/opencode/job_finalize_analysis.py` - mark analysis handoff as ready.

## How to register commands

Run from repository root:

```bash
python tools/opencode/register_project_commands.py
```

This copies files from `tools/opencode/commands/` into:

- `.opencode/commands/`

After this, OpenCode (`Ctrl+K`) will expose `project:e2e:*` commands.

## How to register agent profiles (optional)

If you want to merge profiles into `.opencode.json`:

```bash
python tools/opencode/register_project_commands.py --with-agent-profiles
```

By default, existing profiles are not overwritten.

Overwrite existing profiles:

```bash
python tools/opencode/register_project_commands.py --with-agent-profiles --overwrite-agent-profiles
```

## Example command IDs

- `project:e2e:job:init`
- `project:e2e:job:analyze`
- `project:e2e:job:finalize_analysis`
- `project:e2e:job:implement`
- `project:e2e:job:review`
- `project:e2e:generate_test_from_scenario`
- `project:e2e:subagents:planner`
- `project:e2e:subagents:reviewer`

## Recommended user-agent flow

1. Register assets (`register_project_commands.py`).
2. Run `project:e2e:job:init` once per scenario.
3. Run `project:e2e:job:analyze` (exploratory, multi-page analysis).
4. Answer follow-up questions directly in chat during the analyze job.
5. The agent records answers and finalizes handoff (`project:e2e:job:finalize_analysis`).
6. Run `project:e2e:job:implement`.
7. Run `project:e2e:job:review`.
8. Provide:
   - `SERVER_NAME` (for example `kadwa.zeta`),
   - `SCENARIO_PROMPT` (scenario description).
9. Validate output:
   - `make verify-discovery`
   - `python -m pytest <new_test> -q --server-name=<SERVER_NAME>`

## Job workspace

- Versioned workspace root: `work/e2e-jobs/`.
- One subdirectory per job: `work/e2e-jobs/<job_id>/`.
- Handoff state file: `work/e2e-jobs/<job_id>/handoff/analysis_contract.json`.
- Analysis pass writes notes/cache and captures chat answers for implementation pass in the same job directory.

## Notes

- Runtime builds URLs via `--server-name` and `framework/url_resolver/`.
- Commands and sub-agent prompts are versioned in repo (`tools/opencode`).
- Local `.opencode/` is runtime output and should not be committed.
- Job analysis cache is stored under `work/e2e-jobs/<job_id>/analysis/cache/`.
- Heavy cache files are ignored by `work/e2e-jobs/.gitignore`.
