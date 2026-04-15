# OpenCode Commands For E2E

This directory keeps only simple, interactive OpenCode command assets for E2E work.

Commands are prompt-driven in chat (no env-var input contract).

## What is in this directory

- `tools/opencode/commands/` - command templates copied to `.opencode/commands/`
- `tools/opencode/opencode.agents.json` - optional agent profile presets
- `tools/opencode/register_project_commands.py` - registration helper

No Python helper scripts are required for the E2E job flow.

## Register commands

Run from repository root:

```bash
python tools/opencode/register_project_commands.py
```

This copies command templates from `tools/opencode/commands/` into `.opencode/commands/`.

## Optional: register agent profiles

```bash
python tools/opencode/register_project_commands.py --with-agent-profiles
```

Overwrite existing profile entries:

```bash
python tools/opencode/register_project_commands.py --with-agent-profiles --overwrite-agent-profiles
```

Agent profiles are merged into repo-root `.opencode.json` (not into `.opencode/` directory).

## Active command IDs

- `project:e2e:job:init`
- `project:e2e:job:analyze`
- `project:e2e:job:implement`

## Recommended flow

1. Run `project:e2e:job:init` to create ticket/job context and collect missing data in chat.
2. Run `project:e2e:job:analyze` to perform DOM/behavior analysis and create implementation plan.
3. Run `project:e2e:job:implement` with job context from step 1.

## Job workspace

- Workspace root: `work/e2e-jobs/`
- One directory per job: `work/e2e-jobs/<job_id>/`
- Source of truth: `work/e2e-jobs/<job_id>/ticket.md`
- Analysis artifacts: `work/e2e-jobs/<job_id>/analysis/`
- Implementation notes: `work/e2e-jobs/<job_id>/implementation/`

Artifacts can be saved in separate files, but every created artifact must be referenced in `ticket.md`.

## Remove old local OpenCode assets

If you previously registered old commands/profiles, clean local runtime files and register again:

```bash
rm -rf .opencode/commands/e2e
python tools/opencode/register_project_commands.py --overwrite-commands
```

To remove old agent profile presets from local `.opencode.json`, delete outdated entries under `agents` and keep only what you still use.
