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
  - Manage baseline versions (`create`, `promote`, `list`).
  - Can optionally copy the same operations inside MinIO (`--with-minio`).
- `python tools/visual/retention_baselines.py`
  - Apply retention policy for local baselines/cache and optional MinIO.
  - Defaults: candidates TTL = 7 days, keep 5 latest historical versions per suite.
- `python tools/visual/debug.py`
  - Verify MinIO permissions for readonly/release accounts.
  - `--check-profile auto` (default) always checks list/get and runs release checks only if write access is available.
  - `--check-profile readonly` checks list/get.
  - `--check-profile release` checks list/get/copy/delete using temporary scratch prefix.

## Safety model

- Both write scripts run as `dry-run` by default.
- Use `--apply` to execute file writes.
- Optional `--prune-missing` removes target files that are missing in source.

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
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1 --apply
```

Promote an existing version to `latest`:

```bash
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --apply
```

List available versions:

```bash
python tools/visual/version_baselines.py list
python tools/visual/version_baselines.py list --with-minio
```

## MinIO usage

Add `--with-minio` to `create` or `promote` to copy object keys in MinIO bucket as well.

For local setups without CI, use interactive release credentials prompt:

```bash
python tools/visual/version_baselines.py create \
  --from-version latest \
  --to-version 2026-03-03_1 \
  --with-minio \
  --apply \
  --ask-release-credentials
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
