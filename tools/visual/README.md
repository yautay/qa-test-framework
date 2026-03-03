# Visual Tools

This directory contains helper scripts for local baseline promotion and baseline versioning.

## Scripts

- `python tools/visual/promote_candidates_local.py`
  - Promote local `candidates` baselines to `latest`.
  - Mirrors writes into both:
    - `qa/visual/baselines/<suite>/<profile>/latest/...`
    - `<repo_root>/<VISUAL_CACHE_DIR>/<suite>/<profile>/latest/...`
- `python tools/visual/version_baselines.py`
  - Manage baseline versions (`create`, `promote`, `list`).
  - Can optionally copy the same operations inside MinIO (`--with-minio`).

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
