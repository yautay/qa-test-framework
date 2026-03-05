# Visual Tools

This directory contains helper scripts for local baseline promotion and baseline versioning.

Operator quick procedure: `tools/visual/OPERATOR_RUNBOOK.md`

## Scripts

- `python tools/visual/promote_candidates_local.py`
  - Promote local `candidates` baselines to `latest`.
  - Mirrors writes into both:
    - `qa/visual/baselines/<suite>/<profile>/latest/...`
    - `<repo_root>/<VISUAL_CACHE_DIR>/<suite>/<profile>/latest/...`
- `python tools/visual/version_baselines.py`
  - Manage baseline versions (`create`, `promote`, `recreate`, `clean`, `check`, `list`).
  - Can optionally copy the same operations inside MinIO (`--with-minio`).
  - Internal layout:
    - `version_baselines.py` (CLI entrypoint)
    - `version_baselines_parser.py` (argument parser)
    - `version_baselines_commands.py` (subcommand handlers)
- `python tools/visual/retention_baselines.py`
  - Apply retention policy for local baselines/cache and optional MinIO.
  - Defaults: candidates TTL = 7 days, keep 5 latest historical versions per suite.
- `python tools/visual/debug.py`
  - Verify MinIO permissions for readonly/release accounts.
  - `--check-profile auto` (default) always checks list/get and runs release checks only if write access is available.
  - `--check-profile readonly` checks list/get.
  - `--check-profile release` checks list/get/copy/delete using temporary scratch prefix.
  - Internal layout:
    - `debug.py` (CLI entrypoint)
    - `debug_helpers.py` (endpoint/auth/masking helpers)
    - `debug_checks.py` (permission check execution)

## Internal module layout

`tools/visual/baseline_ops/` is split by responsibility:

- `versioning.py` - compatibility re-export used by existing imports.
- `version_copy.py` - create/promote copy flows + optional MinIO sync.
- `lifecycle_ops.py` - recreate, clean, and consistency check flows.
- `listing_ops.py` - list local and MinIO versions.
- `scan_ops.py` - local/cache/MinIO scanning helpers.
- `models.py` - result dataclasses (`VersioningResult`, `CleanResult`, `CheckResult`).
- existing low-level modules remain in place (`executor.py`, `manifest.py`, `minio_ops.py`, `paths.py`, `scanner.py`, `retention.py`, `types.py`).

## Safety model

- Both write scripts run as `dry-run` by default.
- Use `--apply` in `promote_candidates_local.py` and `--force` in `version_baselines.py`.
- Optional `--prune-missing` removes target files that are missing in source.

## Debug MinIO permissions

Use `debug.py` to validate policy permissions before running write flows.

Notes:

- `--src-key` and `--dst-key` are required by CLI.
- For `--check-profile release` and `--check-profile auto`, writes use a temporary key under `--scratch-prefix`.

```bash
# Auto mode (default): list/get always, release checks only when writes are allowed
python tools/visual/debug.py --src-key qa/visual/baselines/sample_suite/default/latest/sample.png --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png

# Readonly policy: list/get only
python tools/visual/debug.py \
  --check-profile readonly \
  --src-key qa/visual/baselines/sample_suite/default/latest/sample.png \
  --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png

# Release policy: list/get/copy/delete with prompt credentials
python tools/visual/debug.py \
  --check-profile release \
  --ask-release-credentials \
  --src-key qa/visual/baselines/sample_suite/default/latest/sample.png \
  --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png
```

## Promote candidates to latest

```bash
python tools/visual/promote_candidates_local.py
python tools/visual/promote_candidates_local.py --apply
python tools/visual/promote_candidates_local.py --suite netcorner_nuxt_pl_hero_page --apply
python tools/visual/promote_candidates_local.py --prune-missing --apply
```

## Versioning flows

Create a new version from current `latest`:

```bash
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1 --force
```

Promote an existing version to `latest`:

```bash
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --force
```

List available versions:

```bash
python tools/visual/version_baselines.py list
python tools/visual/version_baselines.py list --with-minio
```

Clean local baseline files:

```bash
# Dry-run: clean selected tag (default latest)
python tools/visual/version_baselines.py clean

# Apply: clean all tags from local baselines and cache
python tools/visual/version_baselines.py clean --all --force

# Apply: clean only cache for selected tag
python tools/visual/version_baselines.py clean --tag 2026-03-03_1 --cache --force

# Apply: clean selected MinIO tag (release credentials)
python tools/visual/version_baselines.py clean --tag 2026-03-03_1 --with-minio --force --ask-release-credentials

# Safety override required to delete latest in MinIO
python tools/visual/version_baselines.py clean --tag latest --with-minio --allow-latest-minio-delete --force --ask-release-credentials

# Verify local+cache vs MinIO (default: checksum for each file)
python tools/visual/version_baselines.py check --tag 2026-03-03_1

# Faster verify (presence + size only)
python tools/visual/version_baselines.py check --tag 2026-03-03_1 --fast
```

Make helper:

```bash
make clean-visual-baselines
make clean
```

## MinIO usage

Add `--with-minio` to `create` or `promote` to copy object keys in MinIO bucket as well.

For `clean` with MinIO:

- `--with-minio --all` is blocked for safety.
- deleting MinIO `latest` requires explicit `--allow-latest-minio-delete`.

Use `recreate` to initialize local tester environment from MinIO for a selected tag (or `latest` by default).
`--from-version` is supported as an alias to `--tag`.

For local setups without CI, use interactive release credentials prompt:

```bash
python tools/visual/version_baselines.py create \
  --from-version latest \
  --to-version 2026-03-03_1 \
  --with-minio \
  --force \
  --ask-release-credentials
```

```bash
# Pull exact tag to local baseline/cache (tag -> tag)
python tools/visual/version_baselines.py recreate --tag 2026-03-03_1 --force

# Pull latest when tag is omitted
python tools/visual/version_baselines.py recreate --force

# Full sync with local cleanup
python tools/visual/version_baselines.py recreate --tag 2026-03-03_1 --prune-missing --force

# Disable progress output (CI logs)
python tools/visual/version_baselines.py recreate --tag 2026-03-03_1 --no-progress --force
```

`--prune-missing` prunes targets in local storage, cache mirror, and MinIO (when `--with-minio`).

## Retention policy

Default policy:

- candidates TTL: 7 days,
- keep 5 latest historical versions per suite,
- `latest` is never removed by retention.

Run retention in dry-run mode:

```bash
python tools/visual/retention_baselines.py
```

Apply retention locally and in MinIO:

```bash
python tools/visual/retention_baselines.py \
  --with-minio \
  --apply \
  --ask-release-credentials
```

Required env (from `.env`/environment):

- `VISUAL_MINIO_ENDPOINT`
- `VISUAL_MINIO_BUCKET`
- `VISUAL_MINIO_ACCESS_KEY`
- `VISUAL_MINIO_SECRET_KEY`
- `VISUAL_MINIO_SECURE`

## Manifest output

`create` and `promote` write manifest files to:

`qa/visual/baselines/_manifests/<profile>/<version>.json`

Manifest includes:

- `file_count`
- `total_size_bytes`
- `total_size_mib`
- per-suite size summary (`suite_size_bytes`, `suite_size_mib`)
- per-file rows with `object_key` and `size_bytes`
